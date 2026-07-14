const fs = require('fs');
const path = require('path');

const dir = '/Users/navdeeop/Developer/Internship_2/Project_1/frontend/src/components/dashboard';
const files = fs.readdirSync(dir).filter(f => f.endsWith('.tsx'));

for (const file of files) {
  const filepath = path.join(dir, file);
  let content = fs.readFileSync(filepath, 'utf8');
  
  // Replacements
  content = content.replace(/text-emerald-600/g, 'text-emerald-600 dark:text-emerald-400');
  content = content.replace(/text-emerald-700/g, 'text-emerald-700 dark:text-emerald-300');
  content = content.replace(/text-emerald-800/g, 'text-emerald-800 dark:text-emerald-200');
  content = content.replace(/text-red-600/g, 'text-destructive');
  content = content.replace(/text-red-700/g, 'text-destructive');
  content = content.replace(/text-orange-600/g, 'text-orange-600 dark:text-orange-400');
  content = content.replace(/text-yellow-600/g, 'text-yellow-600 dark:text-yellow-400');
  
  content = content.replace(/bg-red-500/g, 'bg-destructive');
  content = content.replace(/bg-emerald-500/g, 'bg-emerald-500 dark:bg-emerald-400');
  
  fs.writeFileSync(filepath, content);
}
console.log("Colors fixed.");
