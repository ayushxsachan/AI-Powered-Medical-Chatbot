from pathlib import Path


REQUIRED = [
    "backend/app/main.py",
    "backend/app/models/user.py",
    "backend/app/services/medical_response.py",
    "backend/app/datasets/knowledge_initializer.py",
    "backend/app/workers/tasks.py",
    "frontend/app.py",
    "docker-compose.yml",
    "data/raw/disease_symptoms.csv",
]


def main() -> None:
    missing = [path for path in REQUIRED if not Path(path).exists()]
    if missing:
        raise SystemExit(f"Missing required files: {missing}")
    print("Project structure verified")


if __name__ == "__main__":
    main()
