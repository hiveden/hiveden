
package docker

import (
	"context"
	"errors"
	"io"
	"testing"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/image"
	"github.com/docker/docker/api/types/network"
	v1 "github.com/opencontainers/image-spec/specs-go/v1"
)

type mockClient struct {
	createContainerErr bool
	startContainerErr  bool
	stopContainerErr   bool
	removeContainerErr bool
	listContainersErr  bool
	lastCreateConfig   *container.Config
	ContainerListFunc  func(ctx context.Context, options container.ListOptions) ([]types.Container, error)
}

func (m *mockClient) ContainerCreate(ctx context.Context, config *container.Config, hostConfig *container.HostConfig, networkingConfig *network.NetworkingConfig, platform *v1.Platform, containerName string) (container.CreateResponse, error) {
	if m.createContainerErr {
		return container.CreateResponse{}, errors.New("failed to create container")
	}
	m.lastCreateConfig = config
	return container.CreateResponse{ID: "12345"}, nil
}

func (m *mockClient) ContainerStart(ctx context.Context, containerID string, options container.StartOptions) error {
	if m.startContainerErr {
		return errors.New("failed to start container")
	}
	return nil
}

func (m *mockClient) ContainerStop(ctx context.Context, containerID string, options container.StopOptions) error {
	if m.stopContainerErr {
		return errors.New("failed to stop container")
	}
	return nil
}

func (m *mockClient) ContainerRemove(ctx context.Context, containerID string, options container.RemoveOptions) error {
	if m.removeContainerErr {
		return errors.New("failed to remove container")
	}
	return nil
}

func (m *mockClient) ContainerList(ctx context.Context, options container.ListOptions) ([]types.Container, error) {
	if m.ContainerListFunc != nil {
		return m.ContainerListFunc(ctx, options)
	}
	if m.listContainersErr {
		return nil, errors.New("failed to list containers")
	}
	return []types.Container{
		{ID: "1234567890ab", Names: []string{"/test-container"}},
	}, nil
}

func (m *mockClient) ImagePull(ctx context.Context, ref string, options image.PullOptions) (io.ReadCloser, error) {
	return nil, nil
}

func TestNewDockerManager(t *testing.T) {
	dm, err := NewDockerManager()
	if err != nil {
		t.Fatalf("NewDockerManager() error = %v", err)
	}
	if dm.cli == nil {
		t.Fatal("expected cli to be initialized")
	}
}

func TestCreateContainer(t *testing.T) {
	mock := &mockClient{}
	dm := &DockerManager{cli: mock}
	_, err := dm.CreateContainer(context.Background(), "test-image", "test-container")
	if err != nil {
		t.Fatalf("CreateContainer() error = %v", err)
	}

	if managedBy, ok := mock.lastCreateConfig.Labels["managed-by"]; !ok || managedBy != "hiveden" {
		t.Errorf("expected managed-by label to be 'hiveden', got '%s'", managedBy)
	}
}

func TestCreateContainerError(t *testing.T) {
	dm := &DockerManager{cli: &mockClient{createContainerErr: true}}
	_, err := dm.CreateContainer(context.Background(), "test-image", "test-container")
	if err == nil {
		t.Fatal("expected an error, but got none")
	}
}

func TestStartContainer(t *testing.T) {
	dm := &DockerManager{cli: &mockClient{}}
	err := dm.StartContainer(context.Background(), "12345")
	if err != nil {
		t.Fatalf("StartContainer() error = %v", err)
	}
}

func TestStartContainerError(t *testing.T) {
	dm := &DockerManager{cli: &mockClient{startContainerErr: true}}
	err := dm.StartContainer(context.Background(), "12345")
	if err == nil {
		t.Fatal("expected an error, but got none")
	}
}

func TestStopContainer(t *testing.T) {
	dm := &DockerManager{cli: &mockClient{}}
	err := dm.StopContainer(context.Background(), "12345")
	if err != nil {
		t.Fatalf("StopContainer() error = %v", err)
	}
}

func TestStopContainerError(t *testing.T) {
	dm := &DockerManager{cli: &mockClient{stopContainerErr: true}}
	err := dm.StopContainer(context.Background(), "12345")
	if err == nil {
		t.Fatal("expected an error, but got none")
	}
}

func TestRemoveContainer(t *testing.T) {
	dm := &DockerManager{cli: &mockClient{}}
	err := dm.RemoveContainer(context.Background(), "12345")
	if err != nil {
		t.Fatalf("RemoveContainer() error = %v", err)
	}
}

func TestRemoveContainerError(t *testing.T) {
	dm := &DockerManager{cli: &mockClient{removeContainerErr: true}}
	err := dm.RemoveContainer(context.Background(), "12345")
	if err == nil {
		t.Fatal("expected an error, but got none")
	}
}

func TestListContainers(t *testing.T) {
	dm := &DockerManager{cli: &mockClient{}}
	containers, err := dm.ListContainers(context.Background(), true)
	if err != nil {
		t.Fatalf("ListContainers() error = %v", err)
	}
	if len(containers) != 1 {
		t.Fatalf("expected 1 container, got %d", len(containers))
	}
}

func TestListContainersWithLabel(t *testing.T) {
	mock := &mockClient{}
	dm := &DockerManager{cli: mock}

	// Mock a container with the managed-by label
	mockContainer := types.Container{
		ID:      "1234567890ab",
		Names:   []string{"/test-container"},
		Image:   "test-image",
		ImageID: "img-123",
		Labels:  map[string]string{"managed-by": "hiveden"},
	}
	mock.ContainerListFunc = func(ctx context.Context, options container.ListOptions) ([]types.Container, error) {
		return []types.Container{mockContainer}, nil
	}

	containers, err := dm.ListContainers(context.Background(), true)
	if err != nil {
		t.Fatalf("ListContainers() error = %v", err)
	}

	if len(containers) != 1 {
		t.Fatalf("expected 1 container, got %d", len(containers))
	}

	if containers[0].ManagedBy != "hiveden" {
		t.Errorf("expected managed-by to be 'hiveden', got '%s'", containers[0].ManagedBy)
	}
}

func TestListContainersError(t *testing.T) {
	dm := &DockerManager{cli: &mockClient{listContainersErr: true}}
	_, err := dm.ListContainers(context.Background(), true)
	if err == nil {
		t.Fatal("expected an error, but got none")
	}
}
