package docker

import (
	"context"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/network"
	"github.com/docker/docker/client"
	v1 "github.com/opencontainers/image-spec/specs-go/v1"
)

type Client interface {
	ContainerCreate(ctx context.Context, config *container.Config, hostConfig *container.HostConfig, networkingConfig *network.NetworkingConfig, platform *v1.Platform, containerName string) (container.CreateResponse, error)
	ContainerStart(ctx context.Context, containerID string, options container.StartOptions) error
	ContainerStop(ctx context.Context, containerID string, options container.StopOptions) error
	ContainerRemove(ctx context.Context, containerID string, options container.RemoveOptions) error
	ContainerList(ctx context.Context, options container.ListOptions) ([]types.Container, error)
}

// DockerManager provides methods to interact with the Docker API.
type DockerManager struct {
	cli Client
}

// NewDockerManager creates a new DockerManager instance.
func NewDockerManager() (*DockerManager, error) {
	cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
	if err != nil {
		return nil, err
	}
	return &DockerManager{cli: cli}, nil
}

// ListContainers lists all containers.
func (dm *DockerManager) ListContainers(ctx context.Context) ([]types.Container, error) {
	return dm.cli.ContainerList(ctx, container.ListOptions{})
}

// CreateContainer creates a new container.
func (dm *DockerManager) CreateContainer(ctx context.Context, imageName string, containerName string) (container.CreateResponse, error) {
	return dm.cli.ContainerCreate(ctx, &container.Config{
		Image: imageName,
	}, nil, nil, nil, containerName)
}

// StartContainer starts a container.
func (dm *DockerManager) StartContainer(ctx context.Context, containerID string) error {
	return dm.cli.ContainerStart(ctx, containerID, container.StartOptions{})
}

// StopContainer stops a container.
func (dm *DockerManager) StopContainer(ctx context.Context, containerID string) error {
	return dm.cli.ContainerStop(ctx, containerID, container.StopOptions{})
}

// RemoveContainer removes a container.
func (dm *DockerManager) RemoveContainer(ctx context.Context, containerID string) error {
	return dm.cli.ContainerRemove(ctx, containerID, container.RemoveOptions{})
}
