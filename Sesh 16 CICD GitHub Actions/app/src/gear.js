// Static gear list. A real app would read this from a database.
const gear = [
  { id: 1, name: 'Canon EOS 90D camera', category: 'camera', available: true },
  { id: 2, name: 'Rode NT-USB microphone', category: 'audio', available: false },
  { id: 3, name: 'Manfrotto tripod', category: 'support', available: true },
  { id: 4, name: 'Epson projector', category: 'display', available: true },
];

function listGear({ availableOnly = false } = {}) {
  return availableOnly ? gear.filter((g) => g.available) : gear;
}

module.exports = { listGear };
