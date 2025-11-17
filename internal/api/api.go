package api

import (
	"net/http"

	"github.com/hiveden/hiveden/internal/docker"

	"github.com/gin-gonic/gin"
)

// APIHandler provides handler functions for the REST API.
type APIHandler struct {
	dm *docker.DockerManager
}

// NewAPIHandler creates a new APIHandler instance.
func NewAPIHandler(dm *docker.DockerManager) *APIHandler {
	return &APIHandler{dm: dm}
}

// ListContainers handles the GET /containers endpoint.
func (h *APIHandler) ListContainers(c *gin.Context) {
containers, err := h.dm.ListContainers(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, containers)
}

// CreateContainer handles the POST /containers endpoint.
func (h *APIHandler) CreateContainer(c *gin.Context) {
	var reqBody struct {
		ImageName     string `json:"imageName"`
		ContainerName string `json:"containerName"`
	}

	if err := c.ShouldBindJSON(&reqBody); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	resp, err := h.dm.CreateContainer(c.Request.Context(), reqBody.ImageName, reqBody.ContainerName)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, resp)
}

// StartContainer handles the POST /containers/{id}/start endpoint.
func (h *APIHandler) StartContainer(c *gin.Context) {
	containerID := c.Param("id")

	if err := h.dm.StartContainer(c.Request.Context(), containerID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.Status(http.StatusNoContent)
}

// StopContainer handles the POST /containers/{id}/stop endpoint.
func (h *APIHandler) StopContainer(c *gin.Context) {
	containerID := c.Param("id")

	if err := h.dm.StopContainer(c.Request.Context(), containerID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.Status(http.StatusNoContent)
}

// RemoveContainer handles the DELETE /containers/{id} endpoint.
func (h *APIHandler) RemoveContainer(c *gin.Context) {
	containerID := c.Param("id")

	if err := h.dm.RemoveContainer(c.Request.Context(), containerID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.Status(http.StatusNoContent)
}
