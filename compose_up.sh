cd backend
docker build . \
-t ticket-rag-backend:v0.1

cd ../frontend
docker build . \
-t ticket-rag-frontend:v0.1

cd ..
docker compose --env-file ./.env.compose up --detach