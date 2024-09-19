# Floy Technical Challenge

## Questions

**1. What were the reasons for your choice of API/protocol/architectural style used for the client-server communication?**

For the client-server communication, I chose HTTP/REST with FastAPI because it's widely adopted, simple to implement, and well-suited for exchanging structured data. The REST approach is stateless, making it efficient for handling multiple concurrent requests. FastAPI's support for asynchronous programming integrates well with Python's asyncio and aiohttp, ensuring smooth communication between the client and server


**2.  As the client and server communicate over the internet in the real world, what measures would you take to secure the data transmission and how would you implement them?**

To secure data transmission, I would implement TLS/SSL encryption by configuring the server to use HTTPS. TLS ensures that communication between the client and server is encrypted, preventing interception or tampering of sensitive data. The server would require a valid SSL certificate to authenticate its identity. Also, I would implement token-based authentication, such as OAuth 2.0, where the client obtains a secure token that must be included in each request. This ensures that only authenticated clients can interact with the server securely.