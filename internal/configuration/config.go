package configuration

// EnvVar represents a key-value pair for an environment variable in the config file.
type EnvVar struct {
	Name  string `yaml:"name" json:"name"`
	Value string `yaml:"value" json:"value"`
}

// ContainerConfig represents a container configuration in the config file.
type ContainerConfig struct {
	Name  string   `yaml:"name" json:"name"`
	Image string   `yaml:"image" json:"image"`
	Env   []EnvVar `yaml:"env,omitempty" json:"env,omitempty"`
}

// DockerConfig represents the docker configuration in the config file.
type DockerConfig struct {
	NetworkID  string            `yaml:"network_id"`
	Containers []ContainerConfig `yaml:"containers"`
}

// Config represents the main configuration structure from the config file.
type Config struct {
	Docker DockerConfig `yaml:"docker"`
}
