# Holly TUI — Makefile
# Mirrors frontend npm scripts

.PHONY: run build test api-full check clean fmt

## Run the TUI in development mode
run:
	cargo run

## Build release binary
build:
	cargo build --release

## Run all tests
test:
	@echo "=== holly-client tests ==="
	cd ../holly-client && cargo test
	@echo ""
	@echo "=== holly-tui tests ==="
	cargo test

## Full API client rebuild (equivalent to npm run api:full)
api-full:
	./scripts/build-api.sh

## Type check without building
check:
	cargo check
	cd ../holly-client && cargo check

## Format code
fmt:
	cargo fmt
	cd ../holly-client && cargo fmt

## Remove build artifacts
clean:
	cargo clean
	cd ../holly-client && cargo clean

## Show help
help:
	@echo "Holly TUI — Available targets:"
	@echo "  make run       — Run TUI (development)"
	@echo "  make build     — Release build"
	@echo "  make test      — Run all tests"
	@echo "  make api-full  — Rebuild API client (like npm run api:full)"
	@echo "  make check     — Type-check without building"
	@echo "  make fmt       — Format source code"
	@echo "  make clean     — Remove build artifacts"
