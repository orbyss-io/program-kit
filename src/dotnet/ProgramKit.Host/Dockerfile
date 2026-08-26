# syntax=docker/dockerfile:1.26@sha256:ecfaec9ed6d810b56388c508f4121597bfbba70d41a6dfeee4d8cad5f295fc32
FROM mcr.microsoft.com/dotnet/sdk:10.0.202@sha256:adc02be8b87957d07208a4a3e51775935b33bad3317de8c45b1e67357b4c073b AS build
WORKDIR /src
COPY . .
RUN dotnet restore ProgramKit.slnx --locked-mode
RUN dotnet publish src/dotnet/ProgramKit.Host/ProgramKit.Host.csproj -c Release --no-restore -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:10.0@sha256:a4556ed033fa96f984bb7a8d348851cb2d36b1281dd2420070045f664fbb5f94 AS final
WORKDIR /app
ENV ASPNETCORE_URLS=http://+:8080 \
    PROGRAMKIT_BUNDLE_PATH=/opt/program-kit/application-bundle.zip \
    PROGRAMKIT_BUNDLE_CACHE=/app/.program-kit/bundles
EXPOSE 8080
COPY --from=build /app/publish ./
RUN mkdir -p /app/.program-kit/bundles /opt/program-kit \
    && chown -R $APP_UID:$APP_UID /app /opt/program-kit
USER $APP_UID
ENTRYPOINT ["dotnet", "ProgramKit.Host.dll"]
