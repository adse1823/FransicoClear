


# Data folders
mkdir -p data/raw data/processed data/bigquery


# Notebooks
mkdir -p notebooks
touch notebooks/{eda.ipynb,build_graph.ipynb,train_model.ipynb}

# Source code
mkdir -p src/data src/modeling src/logic src/simulation src/api
touch src/__init__.py
touch src/data/{ingest.py,preprocess.py}
touch src/modeling/{train.py,evaluate.py}
touch src/logic/{centralized.py,reinforcement.py}
touch src/simulation/simulate.py
touch src/api/{main.py,routes.py}

# Dashboard
mkdir -p dashboard/assets
touch dashboard/streamlit_app.py

# Models
mkdir -p models
touch models/{congestion_model.pkl,model_card.md}

# Cloud deployment config
mkdir -p cloud
touch cloud/{deploy_api.yaml,vertex_ai_config.json,service_account_setup.sh}

# Tests
mkdir -p tests
touch tests/{test_model.py,test_api.py}

# Docs
mkdir -p docs
touch docs/{architecture.md,README.md,results.md,LICENSE}

# Project-level files
touch .gitignore requirements.txt Dockerfile setup.sh README.md
