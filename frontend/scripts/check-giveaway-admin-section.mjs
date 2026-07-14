import { readFileSync } from 'node:fs';
import { strict as assert } from 'node:assert';

const source = readFileSync(new URL('../src/main.js', import.meta.url), 'utf8');

assert.match(source, /<h4>Участники и номера<\/h4>/, 'admin entries section title is rendered');
assert.match(source, /Сначала создайте и сохраните розыгрыш\./, 'new unsaved giveaways show a save-first hint');
assert.match(source, /В этом розыгрыше пока нет номеров/, 'empty entries state is visible');
assert.doesNotMatch(source, /entries\.length\s*>\s*0/, 'entries section is not gated by entries.length > 0');
assert.doesNotMatch(source, /href="\/api\/v1\/admin\/giveaways\/\$\{escapeHtml\(selected\.id\)\}\/entries\/export\.xlsx"/, 'export does not use a direct protected API link');
assert.match(source, /data-admin-giveaway-export="\$\{escapeHtml\(selected\.id\)\}"/, 'export button uses the saved giveaway id');
assert.match(source, /apiFetchResponse\(`\/api\/v1\/admin\/giveaways\/\$\{encodeURIComponent\(giveawayId\)\}\/entries\/export\.xlsx`/, 'export uses the authenticated admin API client');
assert.match(source, /await response\.blob\(\)/, 'export downloads the response as a blob');
assert.match(source, /data-admin-giveaway-recheck="\$\{escapeHtml\(selected\.id\)\}"/, 'recheck button uses the saved giveaway id');
assert.match(source, /type="button" data-admin-giveaway-recheck/, 'recheck button does not submit the giveaway form');
assert.match(source, /syncGiveawayEntriesSelection\(\{ force: true \}\)/, 'opening or saving a giveaway refreshes entries through the selected giveaway sync');
assert.match(source, /loadGiveawayEntries\(selectedId\)/, 'selected giveaway sync loads entries');
assert.match(source, /\[BLOOM_ADMIN_GIVEAWAY_ENTRIES\] request/, 'safe request log is present');
assert.match(source, /\[BLOOM_ADMIN_GIVEAWAY_ENTRIES\] response/, 'safe response log is present');

console.log('admin giveaway entries section regression checks passed');
