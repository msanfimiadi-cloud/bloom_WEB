import { readFileSync } from 'node:fs';
import { strict as assert } from 'node:assert';

const source = readFileSync(new URL('../src/main.js', import.meta.url), 'utf8');

assert.match(source, /<h4>Участники и номера<\/h4>/, 'admin entries section title is rendered');
assert.match(source, /Сначала сохраните розыгрыш, чтобы открыть список участников\./, 'new unsaved giveaways show a save-first hint');
assert.match(source, /В этом розыгрыше пока нет номеров\./, 'empty entries state is visible');
assert.doesNotMatch(source, /entries\.length\s*>\s*0/, 'entries section is not gated by entries.length > 0');
assert.match(source, /href="\/api\/v1\/admin\/giveaways\/\$\{escapeHtml\(selected\.id\)\}\/entries\/export\.xlsx"/, 'export URL uses the saved giveaway id');
assert.match(source, /data-admin-giveaway-recheck="\$\{escapeHtml\(selected\.id\)\}"/, 'recheck button uses the saved giveaway id');
assert.match(source, /type="button" data-admin-giveaway-recheck/, 'recheck button does not submit the giveaway form');
assert.match(source, /loadGiveawayEntries\(giveawayId\)/, 'opening an existing giveaway loads entries');
assert.match(source, /loadGiveawayEntries\(savedGiveawayId\)/, 'saving a giveaway loads entries without a full page reload');
assert.match(source, /\[BLOOM_ADMIN_GIVEAWAY_ENTRIES\] request/, 'safe request log is present');
assert.match(source, /\[BLOOM_ADMIN_GIVEAWAY_ENTRIES\] response/, 'safe response log is present');

console.log('admin giveaway entries section regression checks passed');
