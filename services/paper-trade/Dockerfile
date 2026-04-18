FROM golang:1.22 AS builder
WORKDIR /app
COPY go.mod ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -o /paper-trade ./services/paper-trade/

FROM gcr.io/distroless/static:nonroot
COPY --from=builder /paper-trade /paper-trade
ENTRYPOINT ["/paper-trade"]
