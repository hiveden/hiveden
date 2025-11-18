package docker

import (
	"context"

	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/network"
)

// ContainerInfo holds custom information about a container.
type ContainerInfo struct {
	ID        string
	Image     string
	ImageID   string
	Name      string
	Uptime    string
	ManagedBy string
}

// NetworkInfo holds custom information about a network.
type NetworkInfo struct {
	ID   string
	Name string
}

// Client is an interface for the Docker client.
type Client interface {
	ContainerCreate(ctx context.Context, config *ContainerConfig) (container.CreateResponse, error)
	ContainerStart(ctx context.Context, containerID string, options container.StartOptions) error
	ContainerStop(ctx context.Context, containerID string, options container.StopOptions) error
	ContainerRemove(ctx context.Context, containerID string, options container.RemoveOptions) error
	ContainerList(ctx context.Context, options container.ListOptions) ([]container.Summary, error)
	NetworkCreate(ctx context.Context, name string, options network.CreateOptions) (network.CreateResponse, error)
	NetworkRemove(ctx context.Context, networkID string) error
	NetworkList(ctx context.Context, options network.ListOptions) ([]network.Summary, error)
	NetworkExists(ctx context.Context, networkName string) (bool, error)
}

// EnvVar represents a key-value pair for an environment variable.
type EnvVar struct {
	Name  string `yaml:"name" json:"name"`
	Value string `yaml:"value" json:"value"`
}

// ContainerConfig represents a container in the YAML config file.
type ContainerConfig struct {
	Name  string   `yaml:"name" json:"name"`
	Image string   `yaml:"image" json:"image"`
	Env   []EnvVar `yaml:"env,omitempty" json:"env,omitempty"`
}

// NetworkConfig represents a network in the YAML config file.
type NetworkConfig struct {
	Name string `yaml:"name"`
}
