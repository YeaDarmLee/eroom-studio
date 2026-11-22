// Run with node tests/test_floor_selector.js. Evals the Alpine state object from the public floor plan template.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('app/templates/public/public_floor_plan_component.html', 'utf8');
const m = html.match(/id="floor-plan-section" x-data="(\{[\s\S]*?\})">\s*<h2/);
assert.ok(m, 'x-data block not found');
const state = vm.runInNewContext('(' + m[1].replace('{{ branch.id }}', '1') + ')', {
    fetch: async () => ({ ok: false }), console,
});

assert.deepEqual(['2F', '1F', 'B1', '3F', 'B2'].sort((a, b) => state.floorRank(a) - state.floorRank(b)),
    ['B2', 'B1', '1F', '2F', '3F']);
assert.equal(state.floorLabel('1F'), '1층');
assert.equal(state.floorLabel('B1'), '지하 1층');
assert.equal(state.floorLabel('2층'), '2층');
assert.equal(state.floorLabel('옥탑'), '옥탑');

state.roomsByFloor = {
    '1F': [
        { room_type: 'monthly', status: 'available' },
        { room_type: 'monthly', status: 'occupied', next_available_date: '2026-12-01' },
        { room_type: 'monthly', status: 'occupied' },
        { room_type: 'manager', status: 'available' },
        { room_type: 'time_based', status: 'available' },
    ],
    '2F': [{ room_type: 'monthly', status: 'occupied' }],
};
assert.equal(state.floorAvailableCount('1F'), 2);
assert.equal(state.floorAvailableCount('2F'), 0);
assert.equal(state.floorAvailableCount('9F'), 0);
console.log('floor selector ok');
