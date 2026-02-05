from flask import Blueprint, jsonify
from flask_swagger_ui import get_swaggerui_blueprint

api_docs_bp = Blueprint('api_docs', __name__)

SWAGGER_URL = '/api/docs'
API_URL = '/api/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "SafeHome API"}
)

SWAGGER_SPEC = {
    "swagger": "2.0",
    "info": {
        "title": "SafeHome API",
        "description": "Phone camera-based home security system API",
        "version": "1.0.0"
    },
    "basePath": "/",
    "schemes": ["http", "https"],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using Bearer scheme. Example: 'Bearer {token}'"
        }
    },
    "paths": {
        "/auth/register": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Register new user",
                "parameters": [{
                    "in": "body",
                    "name": "body",
                    "schema": {
                        "type": "object",
                        "required": ["username", "email", "password"],
                        "properties": {
                            "username": {"type": "string"},
                            "email": {"type": "string"},
                            "password": {"type": "string"}
                        }
                    }
                }],
                "responses": {
                    "200": {"description": "Registration successful"},
                    "400": {"description": "Invalid input"}
                }
            }
        },
        "/auth/login": {
            "post": {
                "tags": ["Authentication"],
                "summary": "User login",
                "parameters": [{
                    "in": "body",
                    "name": "body",
                    "schema": {
                        "type": "object",
                        "required": ["email", "password"],
                        "properties": {
                            "email": {"type": "string"},
                            "password": {"type": "string"}
                        }
                    }
                }],
                "responses": {
                    "200": {"description": "Login successful"},
                    "401": {"description": "Invalid credentials"}
                }
            }
        },
        "/camera/add": {
            "post": {
                "tags": ["Camera"],
                "summary": "Add new camera",
                "security": [{"Bearer": []}],
                "parameters": [{
                    "in": "body",
                    "name": "body",
                    "schema": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {"type": "string"},
                            "location": {"type": "string"}
                        }
                    }
                }],
                "responses": {
                    "200": {"description": "Camera added"},
                    "400": {"description": "Invalid input"},
                    "401": {"description": "Unauthorized"}
                }
            }
        },
        "/camera/{camera_id}/process-frame": {
            "post": {
                "tags": ["Camera"],
                "summary": "Process camera frame",
                "security": [{"Bearer": []}],
                "parameters": [
                    {
                        "in": "path",
                        "name": "camera_id",
                        "required": True,
                        "type": "integer"
                    },
                    {
                        "in": "body",
                        "name": "body",
                        "schema": {
                            "type": "object",
                            "required": ["frame"],
                            "properties": {
                                "frame": {"type": "string", "description": "Base64 encoded image"}
                            }
                        }
                    }
                ],
                "responses": {
                    "200": {"description": "Frame processed successfully"},
                    "404": {"description": "Camera not found"}
                }
            }
        },
        "/alerts": {
            "get": {
                "tags": ["Alerts"],
                "summary": "Get all alerts",
                "security": [{"Bearer": []}],
                "responses": {
                    "200": {"description": "List of alerts"}
                }
            }
        },
        "/automation/create": {
            "post": {
                "tags": ["Automation"],
                "summary": "Create automation rule",
                "security": [{"Bearer": []}],
                "parameters": [{
                    "in": "body",
                    "name": "body",
                    "schema": {
                        "type": "object",
                        "required": ["name", "trigger_type", "actions"],
                        "properties": {
                            "name": {"type": "string"},
                            "trigger_type": {"type": "string"},
                            "actions": {"type": "array"}
                        }
                    }
                }],
                "responses": {
                    "200": {"description": "Rule created"},
                    "400": {"description": "Invalid input"}
                }
            }
        },
        "/analytics/detections": {
            "get": {
                "tags": ["Analytics"],
                "summary": "Get detection analytics",
                "security": [{"Bearer": []}],
                "parameters": [{
                    "in": "query",
                    "name": "days",
                    "type": "integer",
                    "description": "Number of days to analyze"
                }],
                "responses": {
                    "200": {"description": "Detection statistics"}
                }
            }
        }
    }
}

@api_docs_bp.route('/api/swagger.json')
def swagger_json():
    return jsonify(SWAGGER_SPEC)
