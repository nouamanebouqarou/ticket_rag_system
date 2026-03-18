docker build ./backend/. -t ticket-rag-backend:v0.1

docker build ./frontend/. -t ticket-rag-frontend:v0.1

docker compose --env-file ./.env.compose up --detach

#python scripts/process_tickets.py example_tickets_10.csv