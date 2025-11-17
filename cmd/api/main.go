package main

import (
	"log"

	"github.com/hiveden/hiveden/internal/api"
	"github.com/hiveden/hiveden/internal/docker"

	"github.com/gin-gonic/gin"
)

func main() {
	dockerManager, err := docker.NewDockerManager()
	if err != nil {
		log.Fatalf("Failed to create Docker manager: %v", err)
	}

	apiHandler := api.NewAPIHandler(dockerManager)

	r := gin.Default()
	r.GET("/containers", apiHandler.ListContainers)
	r.POST("/containers", apiHandler.CreateContainer)
	r.POST("/containers/:id/start", apiHandler.StartContainer)
	r.POST("/containers/:id/stop", apiHandler.StopContainer)
	r.DELETE("/containers/:id", apiHandler.RemoveContainer)

	log.Println("Starting API server on :8081")
	if err := r.Run(":8081"); err != nil {
		log.Fatalf("Failed to start API server: %v", err)
	}
}
