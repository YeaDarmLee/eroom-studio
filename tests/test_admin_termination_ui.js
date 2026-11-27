// Run with node tests/test_admin_termination_ui.js.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
let createTab;
let requests = [];
let responseOk = true;
const context = {
    document: { addEventListener: (_, callback) => callback() },
    Alpine: { data: (_, factory) => { createTab = factory; } },
    localStorage: { getItem: () => 'test' },
    window: { showAlert() {} },
    confirm: () => { throw new Error('Termination must use the date modal, not a browser confirm'); },
    console,
    fetch: async (_, options) => {
        requests.push(JSON.parse(options.body));
        return { ok: responseOk, json: async () => ({ error: '테스트 저장 실패' }) };
    }
};
vm.runInNewContext(fs.readFileSync('app/static/js/admin/contracts.js', 'utf8'), context);
(async () => {
    const tab = createTab();
    tab.selectedContract = { status: 'terminate_requested', end_date: '2026-12-31' };
    tab.openTerminationModal();
    assert.equal(tab.terminationModalOpen, true);
    assert.equal(tab.terminationDate, '2026-12-31');
    assert.equal(requests.length, 0);
    tab.closeTerminationModal();
    assert.equal(tab.terminationModalOpen, false);
    assert.equal(requests.length, 0);
    tab.openTerminationModal();
    tab.terminationDate = '2026-11-30';
    tab.loadContracts = async () => {};
    await tab.updateStatus(1, 'terminated');
    assert.equal(tab.terminationModalOpen, false);
    assert.deepEqual(requests.pop(), { status: 'terminated', termination_date: '2026-11-30' });
    await tab.updateStatus(1, 'terminated', true);
    assert.deepEqual(requests.pop(), { status: 'terminated', immediate: true });
    for (const status of ['active', 'waiting_signature']) {
        tab.selectedContract = { status, start_date: '2026-07-15' };
        tab.terminationDate = '2026-11-30';
        await tab.updateStatus(1, 'terminated');
        assert.deepEqual(requests.pop(), { status: 'terminated', termination_date: '2026-11-30' });
        tab.terminationDate = '2026-07-14';
        await tab.updateStatus(1, 'terminated');
        assert.equal(requests.length, 0);
    }
    tab.terminationDate = '';
    await tab.updateStatus(1, 'terminated');
    assert.equal(requests.length, 0);
    tab.selectedContract.end_date = '2026-12-31';
    tab.openTerminationModal();
    responseOk = false;
    await tab.updateStatus(1, 'terminated');
    requests.pop();
    assert.equal(tab.terminationModalOpen, true);
    assert.equal(tab.terminationError, '테스트 저장 실패');
    tab.submittingUpdate = true;
    tab.closeTerminationModal();
    await tab.updateStatus(1, 'terminated');
    assert.equal(tab.terminationModalOpen, true);
    assert.equal(requests.length, 0);
    console.log('PASS: modal open/cancel, selected date, immediate termination, validation, failure recovery, duplicate-submit guard');
})().catch(error => { console.error(error); process.exitCode = 1; });
