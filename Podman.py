import podman
import os
import datetime

class Podman:
    _url = 'unix:///tmp/podman.sock'

    def __init__(self) -> None:
        """
        Initializes the class and establishes a connection to the Podman client.

        The constructor attempts to create a connection to the Podman server
        using the Podman client. During initialization, it verifies the
        connectivity to the Podman server. If the connectivity cannot be
        established, it logs the error details.

        Attributes:
            client: Connection to the Podman client for communicating with
                the Podman server.

        Raises:
            Exception: If a connection to the Podman client cannot be
                established during the initialization process.
        """
        self.honeypot_type = None
        self.port_to_bind = None
        self.container = None
        self.client = podman.PodmanClient(base_url=Podman._url)
        try:
            self.client.ping()
        except Exception as e:
            print(f"Error connecting to Podman: {e}")
            raise

    def _build_image(self, image: str, dockerfile_path: str) -> None:
        """
        Builds a Docker image using the provided image name and Dockerfile path.

        This method utilizes the Docker client to build an image from the specified
        Dockerfile. On successful execution, the image is tagged with the given name.
        In case of a PermissionError, the user is notified to rerun the command
        with escalated privileges.

        :param image: Name of the Docker image to be built.
        :type image: str
        :param dockerfile_path: Path to the directory containing the Dockerfile.
        :type dockerfile_path: str
        :return: None
        """
        try:
            print('Building image...')
            # Build from the current directory with the Dockerfile path specified
            self.client.images.build(
                path=dockerfile_path,  # Path to the Dockerfile directory
                dockerfile='Dockerfile',  # Name of the Dockerfile
                tag=image,
                rm=True,
            )
            print(f"Image '{image}' built successfully.")
        except PermissionError:
            print("Permission denied. Please run with sudo.")
        except Exception as e:
            print(f"Error building image: {e}")


    def create_honeypot(self, honeypot_type: str, port_to_bind: int, cpu_period: int = 100000,
                        cpu_quota: int = 50000, mem_limit: str = '512m', memswap_limit: str =
                        '512m') -> None or object:
        """
        Creates a honeypot container based on the specified type and configuration. This function
        checks if the required image exists or builds it if not already present. It then creates
        a container for the honeypot, applying any specified resource limitations.

        :param honeypot_type: Type of the honeypot to be created (e.g., ssh, http).
        :type honeypot_type: str
        :param port_to_bind: Network port to which the honeypot container will be bound.
        :type port_to_bind: int
        :param cpu_period: The scheduling period for CPU resource allocation, in microseconds.
                           Default is 100000.
        :type cpu_period: int, optional
        :param cpu_quota: The time duration in microseconds provided to the honeypot in each
                          CPU period. Default is 50000.
        :type cpu_quota: int, optional
        :param mem_limit: Maximum memory assigned to the honeypot container (e.g., '512m').
                          Default is '512m'.
        :type mem_limit: str, optional
        :param memswap_limit: Total memory and swap limit assigned to the container
                              (e.g., '512m'). Default is '512m'.
        :type memswap_limit: str, optional
        :return: Returns a container object on successful creation, or None if an
                 error occurs during the process.
        :rtype: None or object
        :raises ValueError: If a container with the same name already exists.
        :raises RuntimeError: If image creation fails after the build process.
        """
        try:
            self.honeypot_type = honeypot_type
            self.port_to_bind = port_to_bind

            image = f'h.i.v.e-image-{honeypot_type}'  # Image name
            path = os.path.join('app/honeypots', honeypot_type)  # Path to the honeypot directory
            config_path = os.path.abspath(os.path.join(path, 'config.yaml'))  # Path to the config file
            container_name = f'{honeypot_type}-{port_to_bind}-honeypot'  # Container name

            # Check if container already exists
            if self.client.containers.exists(container_name):
                raise ValueError(f"Container '{container_name}' already exists.")

            print('Creating honeypot...')

            # Check if image exists or container exists
            if self.client.images.exists(image):
                return self._create_container(
                    image=image,
                    container_name=container_name,
                    port_to_bind=port_to_bind,
                    config_path=config_path,
                    honeypot_type=honeypot_type,
                    cpu_period=cpu_period,
                    cpu_quota=cpu_quota,
                    mem_limit=mem_limit,
                    memswap_limit=memswap_limit
                )
            else:
                print(f"Image '{image}' does not exist. Building the image first.")
                try:
                    self._build_image(image, path)
                    # Check if image now exists before recursive call
                    if self.client.images.exists(image):
                        return self.create_honeypot(honeypot_type, port_to_bind)
                    else:
                        raise RuntimeError(
                            f"Failed to build image '{image}'. Aborting container creation.")
                except Exception as e:
                    print(f"Error in image build process: {str(e)}")
                    return None

        except Exception as e:
            print(f"Error in creating honeypot: {str(e)}")
            return None


    def _create_container(self, image, container_name, port_to_bind, config_path, honeypot_type,
                          cpu_period, cpu_quota, mem_limit, memswap_limit) -> object:
        """
        Function to create and configure a container using the specified parameters. It
        utilizes the Docker client to create a container, set up bindings, resource
        limits, and other properties such as hostname and labels. Additionally, it sets
        a restart policy and applies security options. If the container creation
        fails, the function handles the exceptions gracefully.

        :param image: The name of the Docker image to use for creating the container.
        :type image: str
        :param container_name: The desired name for the created container.
        :type container_name: str
        :param port_to_bind: The host port to bind to the container's port 22 (SSH).
        :type port_to_bind: int
        :param config_path: The local path to the configuration file to bind to the container.
        :type config_path: str
        :param honeypot_type: A label to classify the type of the honeypot within the container.
        :type honeypot_type: str
        :param cpu_period: CPU period limit in microseconds. Used to control CPU usage.
        :type cpu_period: int
        :param cpu_quota: CPU quota in microseconds. Should be used in conjunction with cpu_period.
        :type cpu_quota: int
        :param mem_limit: The memory limit assigned to the container (e.g., "512m", "1g").
        :type mem_limit: str
        :param memswap_limit: The memory + swap limit for the container (e.g., "1g", "2g").
        :type memswap_limit: str
        :return: The created container object if successful, None otherwise.
        :rtype: docker.models.containers.Container
        """
        try:
            self.container = self.client.containers.create(
                image=image,
                name=container_name,
                hostname=container_name,
                detach=True,
                ports={'22/tcp': port_to_bind},
                volumes={
                    config_path: {
                        'bind': '/app/config.yaml',
                        'mode': 'rw'
                    }
                },
                labels={
                    'hive.honeypot': honeypot_type,
                    'hive.port': str(port_to_bind),
                },
                cpu_period=cpu_period,  # CPU period in microseconds
                cpu_quota=cpu_quota,  # CPU quota in microseconds
                mem_limit=mem_limit,  # Memory limit
                memswap_limit=memswap_limit,  # Secondary memory limit
                security_opt=['no-new-privileges'],
                restart_policy={'Name': 'always'}
            )

            print(f"Container '{self.container.name}' created successfully.")
            return self.container  # Return the container object

        except PermissionError:
            print("Permission denied. Please run with sudo.")
            return None
        except Exception as e:
            print(f"Error creating container: {str(e)}")
            return None


    def start_honeypot(self) -> bool:
        """
        Attempts to start the honeypot contained within the configured container.
        This method ensures the associated container is started and operational,
        providing feedback for success or failure based on the container's state.
        If an exception occurs during the startup process, it will capture and
        output the error message.

        :return: Indicates whether the honeypot was successfully started.
        :rtype: bool
        """
        try:
            print('Starting honeypot...')
            self.container.start()
            print(f'Honeypot \'{self.container.name}\' started successfully.')
            return True
        except Exception as e:
            print(f"Error starting container: {e}")
            return False



