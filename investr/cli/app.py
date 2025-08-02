"""CLI application for interacting with the investment research agent."""

import uuid

import requests

from investr.common.schemas import AgentResponse, UserRequest


class CLIApp:
    """Command-line interface for investment research agent."""

    def __init__(self, agent_api_url: str = "http://localhost:8000") -> None:
        """Initialize the CLI application.

        Args:
            agent_api_url: URL of the agent API service

        """
        self.agent_api_url: str = agent_api_url
        self.session_id = str(uuid.uuid4())

    def send(self, message: str) -> AgentResponse:
        """Send a message to the agent and return the response.

        Args:
            message: Message to send to the agent

        Returns:
            AgentResponse from the agent API

        Raises:
            Exception: If the request fails or times out

        """
        user_request = UserRequest(session_id=self.session_id, message=message)

        try:
            response: requests.Response = requests.post(
                f"{self.agent_api_url}/agent/query",
                json=user_request.model_dump(),
                timeout=30,
            )

            if response.status_code == 200:
                agent_response = AgentResponse(**response.json())
                return agent_response
            else:
                raise Exception(f"API request failed: {response.text}")

        except requests.exceptions.ConnectionError:
            raise Exception(f"Could not connect to agent API at {self.agent_api_url}")
        except requests.exceptions.Timeout:
            raise Exception("Request timed out after 30 seconds")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")


if __name__ == "__main__":
    app = CLIApp()
    message: str = input("Enter your message: ")
    try:
        agent_response: AgentResponse = app.send(message)
        print("\n" + "=" * 60)
        print("AGENT RESPONSE")
        print("=" * 60)
        print(agent_response.message)
        print("=" * 60)
    except Exception as e:
        print(f"Error: {e}")
