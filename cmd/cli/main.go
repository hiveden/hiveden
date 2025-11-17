package main

import (
	"fmt"
	"log"
	"os"

	"github.com/hiveden/hiveden/internal/docker"

	"github.com/spf13/cobra"
)

func main() {
	dockerManager, err := docker.NewDockerManager()
	if err != nil {
		log.Fatalf("Failed to create Docker manager: %v", err)
	}

	rootCmd := &cobra.Command{Use: "go-docker-manager"}

	rootCmd.AddCommand(buildListCommand(dockerManager))
	rootCmd.AddCommand(buildCreateCommand(dockerManager))
	rootCmd.AddCommand(buildStartCommand(dockerManager))
	rootCmd.AddCommand(buildStopCommand(dockerManager))
	rootCmd.AddCommand(buildRemoveCommand(dockerManager))

	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

func buildListCommand(dm *docker.DockerManager) *cobra.Command {
	return &cobra.Command{
		Use:   "list",
		Short: "List all containers",
		RunE: func(cmd *cobra.Command, args []string) error {
			containers, err := dm.ListContainers(cmd.Context())
			if err != nil {
				return err
			}

			for _, container := range containers {
				fmt.Printf("ID: %s, Image: %s, Status: %s\n", container.ID[:12], container.Image, container.Status)
			}

			return nil
		},
	}
}

func buildCreateCommand(dm *docker.DockerManager) *cobra.Command {
	var imageName, containerName string

	cmd := &cobra.Command{
		Use:   "create",
		Short: "Create a new container",
		RunE: func(cmd *cobra.Command, args []string) error {
			resp, err := dm.CreateContainer(cmd.Context(), imageName, containerName)
			if err != nil {
				return err
			}

			fmt.Printf("Container created with ID: %s\n", resp.ID)
			return nil
		},
	}

	cmd.Flags().StringVar(&imageName, "image", "", "Image name for the container")
	cmd.Flags().StringVar(&containerName, "name", "", "Name for the container")
	cmd.MarkFlagRequired("image")

	return cmd
}

func buildStartCommand(dm *docker.DockerManager) *cobra.Command {
	return &cobra.Command{
		Use:   "start [containerID]",
		Short: "Start a container",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return dm.StartContainer(cmd.Context(), args[0])
		},
	}
}

func buildStopCommand(dm *docker.DockerManager) *cobra.Command {
	return &cobra.Command{
		Use:   "stop [containerID]",
		Short: "Stop a container",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return dm.StopContainer(cmd.Context(), args[0])
		},
	}
}

func buildRemoveCommand(dm *docker.DockerManager) *cobra.Command {
	return &cobra.Command{
		Use:   "remove [containerID]",
		Short: "Remove a container",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return dm.RemoveContainer(cmd.Context(), args[0])
		},
	}
}
