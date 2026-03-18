docker build ./backend/. -t ticket-rag-backend:v0.2

docker build ./frontend/. -t ticket-rag-frontend:v0.1

docker compose --env-file ./.env.compose up --detach

#docker ps
#docker cp /Users/nouamane_bq/Desktop/ResolvedTickes/ticket_rag_system/data/TT_tests.csv 392679ce9cad:/app/TT_tests.csv
#python scripts/process_tickets.py TT_tests.csv