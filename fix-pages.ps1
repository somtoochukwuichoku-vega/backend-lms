# PowerShell script to fix authentication pages
# Run this with: powershell -ExecutionPolicy Bypass -File fix-pages.ps1

$filesToFix = @(
    "src/app/dashboard/page.tsx",
    "src/app/profile/page.tsx",
    "src/app/organizations/page.tsx",
    "src/app/courses/page.tsx",
    "src/app/courses/[id]/page.tsx",
    "src/app/checkout/[courseId]/page.tsx",
    "src/app/assignments/page.tsx"
)

Write-Host "🔧 Starting to fix authentication pages...`n" -ForegroundColor Cyan

$fixedCount = 0

foreach ($file in $filesToFix) {
    if (Test-Path $file) {
        Write-Host "Processing: $file" -ForegroundColor Yellow
        
        $content = Get-Content $file -Raw
        $originalContent = $content
        $modified = $false

        # Fix 1: Add isInitialized to destructuring if not present
        if ($content -match 'const \{isAuthenticated' -and $content -notmatch 'isInitialized') {
            $content = $content -replace 'const \{isAuthenticated(.*?)\} = useAuthStore\(\);', 'const {isAuthenticated, isInitialized$1} = useAuthStore();'
            $modified = $true
            Write-Host "  ✓ Added isInitialized to destructuring" -ForegroundColor Green
        }

        # Fix 2: Add guard to useEffect if not present
        if ($content -notmatch 'if \(!isInitialized\) return;') {
            # Pattern with token check
            $content = $content -replace '(useEffect\(\(\) => \{)\s*(const token[^\}]*\})?\s*(if \(!isAuthenticated\))', '$1`n        if (!isInitialized) return;`n        `n        $3'
            
            # Pattern without token check
            $content = $content -replace '(useEffect\(\(\) => \{)\s*(if \(!isAuthenticated\))', '$1`n        if (!isInitialized) return;`n        `n        $2'
            
            $modified = $true
            Write-Host "  ✓ Added isInitialized guard" -ForegroundColor Green
        }

        # Fix 3: Add isInitialized to dependency array
        if ($content -match '\}, \[isAuthenticated, router' -and $content -notmatch '\[isAuthenticated, isInitialized, router') {
            $content = $content -replace '\}, \[isAuthenticated, router(.*?)\]\);', '}, [isAuthenticated, isInitialized, router$1]);'
            $modified = $true
            Write-Host "  ✓ Updated dependency array" -ForegroundColor Green
        }

        if ($modified -and $content -ne $originalContent) {
            Set-Content -Path $file -Value $content -NoNewline
            Write-Host "  ✅ Fixed $file`n" -ForegroundColor Green
            $fixedCount++
        } else {
            Write-Host "  ⏭️  Skipped (already fixed or pattern not found)`n" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ❌ File not found: $file`n" -ForegroundColor Red
    }
}

Write-Host "`n✨ Done! Fixed $fixedCount out of $($filesToFix.Count) files." -ForegroundColor Cyan
Write-Host "`n📝 Note: The login function in src/store/authStore.ts has already been fixed." -ForegroundColor Yellow
Write-Host "   It now sets isInitialized: true after successful login.`n" -ForegroundColor Yellow
