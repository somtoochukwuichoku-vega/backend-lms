// Run this script with: node fix-pages.js
// This will automatically update all pages with the isInitialized guard

const fs = require('fs');
const path = require('path');

const filesToFix = [
    'src/app/dashboard/page.tsx',
    'src/app/profile/page.tsx',
    'src/app/organizations/page.tsx',
    'src/app/courses/page.tsx',
    'src/app/courses/[id]/page.tsx',
    'src/app/checkout/[courseId]/page.tsx',
    'src/app/assignments/page.tsx',
];

function fixFile(filePath) {
    try {
        let content = fs.readFileSync(filePath, 'utf8');
        let modified = false;

        // Pattern 1: Add isInitialized to destructuring
        if (content.includes('const {isAuthenticated') && !content.includes('isInitialized')) {
            content = content.replace(
                /const \{isAuthenticated(.*?)\} = useAuthStore\(\);/,
                'const {isAuthenticated, isInitialized$1} = useAuthStore();',
            );
            modified = true;
            console.log(`✓ Added isInitialized to ${filePath}`);
        }

        // Pattern 2: Add guard to useEffect
        if (!content.includes('if (!isInitialized) return;')) {
            // Find useEffect with isAuthenticated check
            content = content.replace(
                /(useEffect\(\(\) => \{)\s*(const token[^}]*\})?\s*(if \(!isAuthenticated\))/,
                '$1\n        if (!isInitialized) return;\n        \n        $3',
            );

            // Also handle the simpler pattern without token check
            content = content.replace(
                /(useEffect\(\(\) => \{)\s*(if \(!isAuthenticated\))/,
                '$1\n        if (!isInitialized) return;\n        \n        $2',
            );
            modified = true;
            console.log(`✓ Added isInitialized guard to ${filePath}`);
        }

        // Pattern 3: Add isInitialized to dependency array
        content = content.replace(/\}, \[isAuthenticated, router(.*?)\]\);/g, '}, [isAuthenticated, isInitialized, router$1]);');

        if (modified) {
            fs.writeFileSync(filePath, content, 'utf8');
            console.log(`✅ Fixed ${filePath}\n`);
            return true;
        } else {
            console.log(`⏭️  Skipped ${filePath} (already fixed or pattern not found)\n`);
            return false;
        }
    } catch (error) {
        console.error(`❌ Error fixing ${filePath}:`, error.message);
        return false;
    }
}

console.log('🔧 Starting to fix authentication pages...\n');

let fixedCount = 0;
filesToFix.forEach((file) => {
    if (fixFile(file)) {
        fixedCount++;
    }
});

console.log(`\n✨ Done! Fixed ${fixedCount} out of ${filesToFix.length} files.`);
console.log('\n📝 Note: The login function in src/store/authStore.ts has already been fixed to set isInitialized: true');
