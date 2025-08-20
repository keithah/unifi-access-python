# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-20

### Added
- Initial release of UniFi Access Python SDK
- Complete support for UniFi Access Developer API endpoints
- Async/await architecture for high performance
- Full type hints for better development experience
- Comprehensive error handling with specific exception types
- Bearer token authentication support
- SSL support for self-signed certificates

### Supported Operations
- **Visitors**: Complete CRUD operations, PIN management
- **Doors**: Status retrieval, information queries
- **Devices**: Discovery, monitoring (Access Hubs, Door Readers)
- **Access Policies**: Management, door group associations
- **Door Groups**: Management, door assignments

### Features
- Production-ready codebase
- Comprehensive documentation with examples
- Three detailed usage examples:
  - Basic usage demonstration
  - Visitor management workflows
  - Error handling best practices
- MIT license
- PyPI package ready
- GitHub Actions CI/CD pipeline
- Full test coverage

### API Compatibility
- Tested against real UniFi Access systems
- Compatible with UniFi Access Developer API v1
- Proper handling of API limitations:
  - Door unlock/lock operations (not available in developer API)
  - WebSocket functionality (not available in developer API)
  - Advanced scheduling features (not available in developer API)

### Dependencies
- Python 3.7+
- aiohttp >= 3.8.0
- aiofiles >= 0.8.0

### Development Dependencies
- pytest >= 6.0
- pytest-asyncio >= 0.18.0
- pytest-cov >= 3.0.0
- black >= 22.0.0
- isort >= 5.10.0
- flake8 >= 4.0.0
- mypy >= 0.950
- pre-commit >= 2.17.0