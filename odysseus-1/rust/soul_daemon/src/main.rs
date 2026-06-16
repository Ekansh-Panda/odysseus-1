#![deny(unsafe_code)]

use std::error::Error;
use serde::{Deserialize, Serialize};
use tracing::{info, error, debug};
use tokio::sync::mpsc;

#[derive(Serialize, Deserialize, Debug)]
struct SoulRequest {
    input: String,
    dag: serde_json::Value,
    state: serde_json::Value,
}

#[derive(Serialize, Deserialize, Debug)]
struct SoulResponse {
    text: String,
    state_delta: serde_json::Value,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    tracing_subscriber::fmt::init();
    info!("Soul Daemon v5.0 starting...");

    let context = zmq::Context::new();
    let responder = context.socket(zmq::REP)?;
    responder.bind("tcp://*:5555")?;

    let control = context.socket(zmq::PULL)?;
    control.bind("tcp://*:5556")?;

    info!("Soul Daemon listening on ports 5555 (REP) and 5556 (PULL)");

    loop {
        // Check for control messages (non-blocking)
        if let Ok(msg) = control.recv_bytes(zmq::DONTWAIT) {
            info!("Received control message: {:?}", String::from_utf8_lossy(&msg));
        }

        // Handle inference requests
        let msg = match responder.recv_bytes(0) {
            Ok(m) => m,
            Err(e) => {
                error!("ZMQ recv error: {}", e);
                continue;
            }
        };

        let req: SoulRequest = match serde_json::from_slice(&msg) {
            Ok(r) => r,
            Err(e) => {
                error!("Failed to parse request: {}", e);
                let err_resp = serde_json::to_vec(&serde_json::json!({"error": "invalid_json"}))?;
                responder.send(err_resp, 0)?;
                continue;
            }
        };

        debug!("Inference for: {}", req.input);

        // Simulation of Llama-cpp inference
        let response = SoulResponse {
            text: format!("Soul Engine response to: {}", req.input),
            state_delta: serde_json::json!({
                "working_memory": [format!("User said: {}", req.input)]
            }),
        };

        let resp_bytes = serde_json::to_vec(&response)?;
        responder.send(resp_bytes, 0)?;
    }
}
