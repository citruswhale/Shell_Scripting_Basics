const { createApp } = require('./app');

const port = Number(process.env.PORT) || 3000;

const server = createApp().listen(port, () => {
  console.log(`gear-api listening on port ${port}`);
});

// Kubernetes sends SIGTERM before stopping a pod
process.on('SIGTERM', () => {
  server.close(() => process.exit(0));
});
