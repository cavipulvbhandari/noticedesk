# syntax=docker/dockerfile:1

# ---- Build stage: compile the whole reactor, produce the server fat-jar ----
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /build

# Warm the dependency cache on the pom layer so code changes don't re-download.
COPY pom.xml ./
COPY ocr-core/pom.xml ocr-core/
COPY ocr-server/pom.xml ocr-server/
RUN mvn -q -e -B -pl ocr-core,ocr-server -am dependency:go-offline || true

COPY ocr-core/src ocr-core/src
COPY ocr-server/src ocr-server/src
RUN mvn -q -B -pl ocr-core,ocr-server -am package -DskipTests

# ---- Runtime stage: JRE + Tesseract native + language data -----------------
FROM eclipse-temurin:21-jre-jammy AS runtime

# Tesseract 5 (via the OCR PPA-free jammy packages) plus English and Hindi
# language data. Hindi matters for Indian tax notices; add more (mar, guj, tam…)
# by extending this list — no code change required.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-hin \
        libtesseract5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Tell Tess4J where the language data lives. On jammy the packages install to
# /usr/share/tesseract-ocr/5/tessdata.
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata
ENV OCR_LANGUAGES=eng

WORKDIR /app
COPY --from=build /build/ocr-server/target/ocr-server.jar app.jar

# Run as non-root.
RUN useradd --system --uid 10001 ocr && chown ocr:ocr /app
USER ocr

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["sh", "-c", "curl -fsS http://localhost:8080/health || exit 1"]

ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "app.jar"]
