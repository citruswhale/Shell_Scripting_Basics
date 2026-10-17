const express = require('express');
const { listGear } = require('./gear');
const pkg = require('../package.json');

// Build the Express app. Kept separate from server.js so tests can start it on a random port.
function createApp() {
  const app = express();

  app.get('/', (req, res) => {
    res.json({
      app: pkg.name,
      version: pkg.version,
      // APP_COMMIT is set by the CD job to the Git SHA of the image
      commit: process.env.APP_COMMIT || 'local',
    });
  });

  app.get('/health', (req, res) => {
    res.json({ status: 'ok' });
  });

  app.get('/api/gear', (req, res) => {
    const availableOnly = req.query.available === 'true';
    const items = listGear({ availableOnly });
    res.json({ count: items.length, items });
  });

  // Anything else is a 404 in JSON
  app.use((req, res) => {
    res.status(404).json({ error: 'not found' });
  });

  return app;
}

module.exports = { createApp };
