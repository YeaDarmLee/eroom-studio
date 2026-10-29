// Run with node tests/test_admin_termination_ui.js.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
let createTab;
let requests = [];
let approved = true;
const context = {
    document: { addEventListener: (_, callback) => callback() },
    Alpine: { data: (_, factory) => { createTab = factory; } },
    localStorage: { getItem: () => 'test' },
    window: { showAlert() {} },
    confirm: () => approved,
    console,
    fetch: async (_, options) => {
        requests.push(JSON.parse(options.body));
        return { ok: true };
    }
};
vm.runInNewContext(fs.readFileSync('app/static/js/admin/contracts.js', 'utf8'), context);
(async () => {
    const tab = createTab();
    tab.selectedContract = { status: 'terminate_requested' };
    tab.terminationDate = '2026-11-30';
    tab.loadContracts = async () => {};
    await tab.updateStatus(1, 'terminated');
    assert.deepEqual(requests.pop(), { status: 'terminated', termination_date: '2026-11-30' });
    await tab.updateStatus(1, 'terminated', true);
    assert.deepEqual(requests.pop(), { status: 'terminated', immediate: true });
    approved = false;
    await tab.updateStatus(1, 'terminated');
    assert.equal(requests.length, 0);
    approved = true;
    tab.terminationDate = '';
    await tab.updateStatus(1, 'terminated');
    assert.equal(requests.length, 0);
    console.log('PASS: date approval, immediate termination, cancellation, required date');
})().catch(error => { console.error(error); process.exitCode = 1; });
