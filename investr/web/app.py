"""Flask web application for the Investment Research Agent."""

import json
import os
import uuid
from datetime import datetime

import requests
from flask import Flask, Response, jsonify, render_template, request, session

from investr.common.schemas import UserRequest


class WebApp:
    """Flask web application for investment research."""

    def __init__(self, agent_api_url: str = "http://agent:8000"):
        """Initialize the web application.

        Args:
            agent_api_url: URL of the agent API service

        """
        self.agent_api_url = agent_api_url
        self.app = Flask(__name__)
        self.app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Set up Flask routes."""

        @self.app.route("/")
        def index() -> str:
            """Serve main chat interface."""
            if "session_id" not in session:
                session["session_id"] = str(uuid.uuid4())
            return render_template("index.html")

        @self.app.route("/api/chat", methods=["POST"])
        def chat() -> tuple[Response, int] | Response:
            """Handle chat messages from the frontend."""
            try:
                data = request.get_json()
                message = data.get("message", "").strip()

                if not message:
                    return jsonify({"error": "Message cannot be empty"}), 400

                # Get or create session ID
                session_id = session.get("session_id", str(uuid.uuid4()))
                session["session_id"] = session_id

                # Create request for agent API
                user_request = UserRequest(
                    session_id=session_id,
                    message=message,
                    context={"timestamp": datetime.now().isoformat()},
                )

                # Always return streaming response - provides better user experience
                return Response(
                    self._stream_agent_response(user_request),
                    content_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Access-Control-Allow-Origin": "*",
                    },
                )

            except Exception as e:
                return jsonify({"error": f"Failed to process request: {str(e)}"}), 500

        @self.app.route("/api/health")
        def health() -> Response:
            """Health check endpoint."""
            return jsonify(
                {
                    "status": "healthy",
                    "service": "investment-web",
                    "timestamp": datetime.now().isoformat(),
                }
            )

    def _stream_agent_response(self, user_request: UserRequest):
        """Stream agent response from the streaming endpoint.

        Args:
            user_request: The user request to send

        Yields:
            Server-sent events

        """
        try:
            # Call the agent streaming API
            response = requests.post(
                f"{self.agent_api_url}/agent/stream",
                json=user_request.model_dump(),
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=60,
            )

            if response.status_code == 200:
                # Forward the streaming response
                for line in response.iter_lines():
                    if line:
                        yield line.decode("utf-8") + "\n"
            else:
                # Handle API error
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", "Unknown error")
                except:
                    error_detail = f"HTTP {response.status_code}"

                # Send error event
                error_event = {
                    "type": "error",
                    "message": f"Agent API error: {error_detail}",
                }
                yield f"data: {json.dumps(error_event)}\n\n"

        except requests.exceptions.RequestException as e:
            # Handle connection errors
            error_event = {"type": "error", "message": f"Connection error: {str(e)}"}
            yield f"data: {json.dumps(error_event)}\n\n"
        except Exception as e:
            # Handle other errors
            error_event = {"type": "error", "message": f"Unexpected error: {str(e)}"}
            yield f"data: {json.dumps(error_event)}\n\n"

    def run(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False) -> None:
        """Run the Flask application.

        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Whether to run in debug mode

        """
        self.app.run(host=host, port=port, debug=debug)


def create_app() -> Flask:
    """Create and configure the Flask application.

    Returns:
        Configured Flask application

    """
    agent_api_url: str = os.environ.get("AGENT_API_URL", "http://agent:8000")
    web_app = WebApp(agent_api_url=agent_api_url)
    return web_app.app


if __name__ == "__main__":
    app: Flask = create_app()
    port = int(os.environ.get("PORT", 5000))
    debug: bool = os.environ.get("FLASK_ENV") == "development"

    print(f"Starting Investment Research Web UI on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
