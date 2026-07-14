import { readFileSync } from 'node:fs';
import { strict as assert } from 'node:assert';

const main = readFileSync(new URL('../src/main.js', import.meta.url), 'utf8');
const css = readFileSync(new URL('../src/styles.css', import.meta.url), 'utf8');

assert.match(main, /giveaway-participants-table-wrapper/, 'participants table gets a scoped scroll wrapper class');
assert.match(main, /giveaway-participants-table/, 'participants table gets a scoped table class');
assert.match(main, /'admin-table--compact admin-table--giveaway-entries'/, 'participants table is the only giveaway entries table render target');
const allGiveawaysSection = main.slice(main.indexOf('<section class="ui-card giveaway-section"><h4>Все розыгрыши</h4>'), main.indexOf('</section>${renderGiveawayEntriesSection'));
assert.match(allGiveawaysSection, /'admin-table--compact'/, 'All giveaways table keeps the regular compact admin table class');
assert.doesNotMatch(allGiveawaysSection, /admin-table--giveaway-entries|giveaway-participants-table/, 'All giveaways table does not receive wide participants classes');
assert.match(main, /Редактировать/, 'Edit action remains rendered in the All giveaways table');

assert.match(css, /\.giveaway-participants-table-wrapper\s*{[\s\S]*?overflow-x:\s*auto;[\s\S]*?max-width:\s*100%;[\s\S]*?min-width:\s*0;/, 'participants wrapper owns horizontal scrolling and cannot expand parents');
assert.match(css, /\.giveaway-participants-table\s*{[\s\S]*?width:\s*max-content;[\s\S]*?min-width:\s*1700px;/, 'wide min-width is scoped to the participants table');
assert.doesNotMatch(css, /\.(?:admin-table-wrap|admin-table|admin-table--compact)\s*{[^}]*min-width:\s*1[78]00px/i, 'generic admin table wrappers do not receive wide participants min-width');
assert.match(css, /\.admin-dashboard\s*{[\s\S]*?max-width:\s*100%;[\s\S]*?min-width:\s*0;/, 'admin root dashboard stays constrained to viewport width');
assert.match(css, /\.giveaways-page,\s*\n\.giveaway-section,\s*\n\.giveaway-participants-section\s*{[\s\S]*?max-width:\s*100%;[\s\S]*?min-width:\s*0;/, 'giveaway page containers stay constrained and allow child overflow isolation');
assert.match(css, /\.giveaways-page\s*{[\s\S]*?grid-template-columns:\s*minmax\(0, 1fr\);/, 'giveaway page grid track allows children to shrink');
assert.match(css, /\.giveaway-entry-stats\s*{[\s\S]*?flex-wrap:\s*wrap;[\s\S]*?max-width:\s*100%;[\s\S]*?min-width:\s*0;/, 'stats wrap without expanding the page');
assert.match(css, /\.giveaway-participants-section \.admin-toolbar\s*{[\s\S]*?flex-wrap:\s*wrap;/, 'participants export/recheck actions wrap inside the section');
assert.doesNotMatch(css, /body\s*{[^}]*overflow-x:\s*auto/i, 'body does not use page-level horizontal scrolling');
assert.match(css, /html\s*{[^}]*overflow-x:\s*hidden;[\s\S]*body\s*{[^}]*overflow-x:\s*hidden;/, 'document/body hide accidental page overflow while table wrapper remains scrollable');

console.log('giveaway overflow layout regression checks passed');
