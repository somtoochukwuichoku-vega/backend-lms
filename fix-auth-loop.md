# Fix Authentication Refresh Loop

## Problem

Pages are checking `isAuthenticated` before the auth state is initialized from localStorage, causing infinite redirect loops.

## Solution Applied

✅ Updated `src/store/authStore.ts` - Added `isInitialized` property and `initialize()` method
✅ Updated `src/components/AppLayout.tsx` - Calls `initialize()` on mount

## Manual Changes Required

Due to workspace settings restrictions, you need to manually update the following files:

### 1. src/app/dashboard/page.tsx

**Line 16:** Change from:

```typescript
const {isAuthenticated, user} = useAuthStore();
```

To:

```typescript
const {isAuthenticated, isInitialized, user} = useAuthStore();
```

**Lines 20-27:** Change from:

```typescript
useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token || !isAuthenticated) {
        router.push('/login');
        return;
    }
    fetchDashboardData();
}, [isAuthenticated, router]);
```

To:

```typescript
useEffect(() => {
    if (!isInitialized) return;

    if (!isAuthenticated) {
        router.push('/login');
        return;
    }
    fetchDashboardData();
}, [isAuthenticated, isInitialized, router]);
```

### 2. src/app/profile/page.tsx

**Line 14:** Change from:

```typescript
const {isAuthenticated, user, updateProfile, fetchProfile} = useAuthStore();
```

To:

```typescript
const {isAuthenticated, isInitialized, user, updateProfile, fetchProfile} = useAuthStore();
```

**Lines 19-26:** Change from:

```typescript
useEffect(() => {
    if (!isAuthenticated) {
        router.push('/login');
        return;
    }
    if (user) {
        setFormData({first_name: user.first_name || '', last_name: user.last_name || '', bio: user.bio || ''});
    }
}, [isAuthenticated, router, user]);
```

To:

```typescript
useEffect(() => {
    if (!isInitialized) return;

    if (!isAuthenticated) {
        router.push('/login');
        return;
    }
    if (user) {
        setFormData({first_name: user.first_name || '', last_name: user.last_name || '', bio: user.bio || ''});
    }
}, [isAuthenticated, isInitialized, router, user]);
```

### 3. src/app/organizations/page.tsx

**Line 16:** Change from:

```typescript
const {isAuthenticated} = useAuthStore();
```

To:

```typescript
const {isAuthenticated, isInitialized} = useAuthStore();
```

**Lines 27-32:** Change from:

```typescript
useEffect(() => {
    if (!isAuthenticated) {
        router.push('/login');
        return;
    }

    fetchOrganizations();
}, [isAuthenticated, router]);
```

To:

```typescript
useEffect(() => {
    if (!isInitialized) return;

    if (!isAuthenticated) {
        router.push('/login');
        return;
    }

    fetchOrganizations();
}, [isAuthenticated, isInitialized, router]);
```

### 4. src/app/courses/page.tsx

**Line 16:** Change from:

```typescript
const {isAuthenticated} = useAuthStore();
```

To:

```typescript
const {isAuthenticated, isInitialized} = useAuthStore();
```

**Lines 26-31:** Change from:

```typescript
useEffect(() => {
    if (!isAuthenticated) {
        router.push('/login');
        return;
    }

    fetchData();
}, [isAuthenticated, router]);
```

To:

```typescript
useEffect(() => {
    if (!isInitialized) return;

    if (!isAuthenticated) {
        router.push('/login');
        return;
    }

    fetchData();
}, [isAuthenticated, isInitialized, router]);
```

### 5. src/app/courses/[id]/page.tsx

**Line 18:** Change from:

```typescript
const {isAuthenticated} = useAuthStore();
```

To:

```typescript
const {isAuthenticated, isInitialized} = useAuthStore();
```

**Lines 23-28:** Change from:

```typescript
useEffect(() => {
    if (!isAuthenticated) {
        router.push('/login');
        return;
    }

    fetchCourse();
}, [isAuthenticated, router, params.id]);
```

To:

```typescript
useEffect(() => {
    if (!isInitialized) return;

    if (!isAuthenticated) {
        router.push('/login');
        return;
    }

    fetchCourse();
}, [isAuthenticated, isInitialized, router, params.id]);
```

### 6. src/app/checkout/[courseId]/page.tsx

**Line 17:** Change from:

```typescript
const {isAuthenticated} = useAuthStore();
```

To:

```typescript
const {isAuthenticated, isInitialized} = useAuthStore();
```

**Lines 23-28:** Change from:

```typescript
useEffect(() => {
    if (!isAuthenticated) {
        router.push('/login');
        return;
    }

    fetchCourse();
}, [isAuthenticated, router, params.courseId]);
```

To:

```typescript
useEffect(() => {
    if (!isInitialized) return;

    if (!isAuthenticated) {
        router.push('/login');
        return;
    }

    fetchCourse();
}, [isAuthenticated, isInitialized, router, params.courseId]);
```

### 7. src/app/assignments/page.tsx

**Line 15:** Change from:

```typescript
const {isAuthenticated} = useAuthStore();
```

To:

```typescript
const {isAuthenticated, isInitialized} = useAuthStore();
```

**Lines 20-25:** Change from:

```typescript
useEffect(() => {
    if (!isAuthenticated) {
        router.push('/login');
        return;
    }

    fetchAssignments();
}, [isAuthenticated, router]);
```

To:

```typescript
useEffect(() => {
    if (!isInitialized) return;

    if (!isAuthenticated) {
        router.push('/login');
        return;
    }

    fetchAssignments();
}, [isAuthenticated, isInitialized, router]);
```

### 8. Check src/app/courses/[id]/modules/[moduleId]/lessons/[lessonId]/page.tsx

This file also needs the same pattern applied if it exists.

## How It Works

1. When the app loads, `AppLayout` calls `initialize()` which:
    - Checks if there's a token in localStorage
    - If yes, validates it by fetching the user profile
    - Sets `isInitialized: true` when done (success or failure)

2. Pages now wait for `isInitialized` before checking authentication:
    - `if (!isInitialized) return;` - Wait for initialization
    - `if (!isAuthenticated)` - Then check if user is logged in

3. This prevents the redirect loop because pages won't redirect until they know the actual auth state.

## Testing

After making these changes:

1. Clear your browser's localStorage
2. Refresh the page
3. Try logging in
4. Navigate between pages
5. The refresh loop should be gone!
