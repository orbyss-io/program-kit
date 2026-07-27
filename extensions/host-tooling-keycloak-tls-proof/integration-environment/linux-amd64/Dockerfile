FROM mcr.microsoft.com/dotnet/sdk:10.0.302-noble-amd64@sha256:3dae2f7699441af56216ff64d5c9b6dfce7cd7dc7f4f71d353d29662b10a384f AS exact_dotnet_sdk
FROM docker:29.6.2-cli@sha256:feb2d49bd65f274b3e4b4620beabe2f4691e5287e496da9fbc9830ed5f780676 AS exact_docker_cli
FROM mcr.microsoft.com/playwright/dotnet:v1.61.0-noble@sha256:72d804504ac23fcc83c770ca68c88c7e6b3e3462c9ad02f220197b95d46237db

COPY --from=exact_dotnet_sdk /usr/share/dotnet /usr/share/dotnet
COPY --from=exact_docker_cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=exact_docker_cli /usr/local/libexec/docker/cli-plugins/docker-buildx /usr/local/libexec/docker/cli-plugins/docker-buildx

ENV DOTNET_ROOT=/usr/share/dotnet
ENV PATH=/usr/share/dotnet:${PATH}
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /workspace
ENTRYPOINT ["/bin/bash"]
