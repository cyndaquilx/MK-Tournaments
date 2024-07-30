#!/bin/bash
docker cp tournamentbot:/app/tournament_data.pkl .
docker build --tag tournamentbot .
docker stop tournamentbot
docker rm tournamentbot
docker run -d --name tournamentbot --restart unless-stopped tournamentbot