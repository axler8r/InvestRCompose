"""Flask web application for the Investment Research Agent."""

import os
import uuid
from datetime import datetime

import requests
from flask import Flask, jsonify, render_template, request, session

from investr.common.schemas import AgentResponse, RequestStatus, UserRequest


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
        def index():
            """Serve main chat interface."""
            if "session_id" not in session:
                session["session_id"] = str(uuid.uuid4())
            return render_template("index.html")

        @self.app.route("/api/chat", methods=["POST"])
        def chat():
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

                # Send request to agent API
                response = self._call_agent_api(user_request)

                return jsonify(
                    {
                        "response": response.message,
                        "status": response.status.value,
                        "timestamp": response.timestamp.isoformat(),
                        "session_id": response.session_id,
                        "tool_calls": response.tool_calls or [],
                        "references": response.references or [],
                        "metadata": response.metadata or {},
                    }
                )

            except Exception as e:
                return jsonify({"error": f"Failed to process request: {str(e)}"}), 500

        @self.app.route("/api/health")
        def health():
            """Health check endpoint."""
            return jsonify(
                {
                    "status": "healthy",
                    "service": "investment-web",
                    "timestamp": datetime.now().isoformat(),
                }
            )

    def _call_agent_api(self, user_request: UserRequest) -> AgentResponse:
        """Call the agent API with a user request.

        Args:
            user_request: The user request to send

        Returns:
            Agent response

        Raises:
            Exception: If API call fails

        """
        try:
            # Call the agent service API
            response = requests.post(
                f"{self.agent_api_url}/api/query",
                json=user_request.model_dump(),
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                return AgentResponse(**data)
            else:
                # Handle API error
                error_detail = response.json().get("detail", "Unknown error")
                raise Exception(f"Agent API error: {error_detail}")

        except requests.exceptions.RequestException as e:
            # Handle connection errors - return mock response for development
            return AgentResponse(
                session_id=user_request.session_id,
                message=f"I received your message: '{user_request.message}'. "
                f"Currently running in development mode - agent service may not be available. "
                f"Connection error: {str(e)}",
                status=RequestStatus.COMPLETED,
                timestamp=datetime.now(),
                tool_calls=[],
                references=["Development mode"],
                metadata={"error": "agent_unavailable", "mode": "development"},
            )
        except Exception as e:
            # Return error response
            return AgentResponse(
                session_id=user_request.session_id,
                message=f"Sorry, I encountered an error: {str(e)}",
                status=RequestStatus.FAILED,
                timestamp=datetime.now(),
                tool_calls=[],
                references=[],
                metadata={"error": True},
            )

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
    agent_api_url = os.environ.get("AGENT_API_URL", "http://agent:8000")
    web_app = WebApp(agent_api_url=agent_api_url)
    return web_app.app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"

    print(f"Starting Investment Research Web UI on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
