FROM mcr.microsoft.com/dotnet/sdk:10.0.302-noble-amd64@sha256:3dae2f7699441af56216ff64d5c9b6dfce7cd7dc7f4f71d353d29662b10a384f AS exact_dotnet_sdk
FROM mcr.microsoft.com/playwright/dotnet:v1.61.0-noble@sha256:72d804504ac23fcc83c770ca68c88c7e6b3e3462c9ad02f220197b95d46237db

COPY --from=exact_dotnet_sdk /usr/share/dotnet /usr/share/dotnet

ENV DOTNET_ROOT=/usr/share/dotnet
ENV PATH=/usr/share/dotnet:${PATH}
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /workspace
ENTRYPOINT ["/bin/bash"]
