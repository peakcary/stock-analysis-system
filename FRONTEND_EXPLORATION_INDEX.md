# Frontend Exploration Index

This directory contains comprehensive documentation about the stock analysis system frontend and recommendations for building a raw data viewer page.

## Documents Overview

### 1. FRONTEND_ANALYSIS.md (18 KB)
**Comprehensive architectural analysis of the entire frontend**

Contains:
- Frontend project structure and organization
- Pages and routing system (tab-based routing model)
- Analysis of existing data view pages with code patterns
- API integration architecture
- UI/Components framework (Ant Design)
- Available data sources and database models
- Recommended architecture for raw data viewer
- Authentication and authorization flow
- Best practices observed
- Key implementation recommendations

**Read this first** for complete understanding of:
- How pages are organized
- How data flows from API to UI
- What components and patterns are used
- How to structure a new page

### 2. FRONTEND_QUICK_REFERENCE.md (8.3 KB)
**Quick lookup guide with code snippets and patterns**

Contains:
- File locations (absolute paths)
- Common code patterns (fetching, creating pages, menu items)
- React hooks reference
- Ant Design components cheat sheet
- TypeScript interfaces patterns
- API request examples
- Color scheme used
- Development commands
- Data models available
- Error handling pattern
- Component naming conventions

**Use this when you need** to:
- Copy code snippets quickly
- Look up a component API
- Find file locations
- Remember conventions

### 3. RAW_DATA_VIEWER_IMPLEMENTATION.md (12 KB)
**Step-by-step guide for building the raw data viewer page**

Contains:
- Phase 1: Backend API development (endpoints, integration)
- Phase 2: Frontend page development (complete component code)
- Phase 3: Enhanced features (filtering, column selection)
- Implementation checklist
- Common pitfalls to avoid
- API response format specifications
- Future enhancement ideas

**Use this to**:
- Build the raw data viewer from scratch
- Understand the 3-phase approach
- Copy boilerplate code
- Check implementation status

## Quick Navigation

### I want to understand...

| Topic | Document | Section |
|-------|----------|---------|
| Project structure | FRONTEND_ANALYSIS | Section 1 |
| How routing works | FRONTEND_ANALYSIS | Section 2 |
| Example data pages | FRONTEND_ANALYSIS | Section 3 |
| API integration | FRONTEND_ANALYSIS | Section 4 |
| UI components | FRONTEND_ANALYSIS | Section 5 |
| Available data | FRONTEND_ANALYSIS | Section 6 |
| Recommended design | FRONTEND_ANALYSIS | Section 7 |
| Authentication | FRONTEND_ANALYSIS | Section 8 |
| Best practices | FRONTEND_ANALYSIS | Section 9 |

### I want to find...

| Item | Document | Section |
|------|----------|---------|
| File path for X | QUICK_REFERENCE | File Locations |
| Code example for Y | QUICK_REFERENCE | Common Patterns |
| Component API | QUICK_REFERENCE | Ant Design Components |
| How to structure page | IMPLEMENTATION | Phase 2 |
| Backend endpoint code | IMPLEMENTATION | Phase 1.1 |
| Checklist | IMPLEMENTATION | Implementation Checklist |

## Key Findings Summary

### Frontend Stack
- React 18.2 with TypeScript
- Vite 7.1 (build tool)
- Ant Design 5.27 (UI library)
- Axios 1.11 (HTTP client)
- React Router 6.8 (routing)

### Architecture Pattern
- **Tab-based routing** (not traditional URL routing)
- All pages managed in `App.tsx` with `activeTab` state
- Menu click → state change → conditional rendering
- Centralized API client with auto-authentication

### Example Pages Analyzed
1. **StockListPage** - Basic data table with modal detail views
2. **ConceptAnalysisPage** - Concept data with drill-down
3. **UserManagement** - Advanced filtering and pagination

### Common Patterns
1. State: `useState` for data, loading, pagination, filters
2. API: `useEffect` to trigger fetches
3. UI: Ant Design Table + Card + Loading states
4. Pagination: Server-side with skip/limit
5. Errors: Toast messages via `message` component

### Key Files
```
Frontend root: /frontend/src/
Main app: /App.tsx (routing, menu, state)
Pages: /components/*.tsx
Layout: /components/AdminLayout.tsx
Auth: /contexts/AuthContext.tsx + /shared/admin-auth.ts
API: /api/endpoints.ts

Shared: /shared/admin-auth.ts (API client, singleton)
```

## Recommended Approach for Raw Data Viewer

### Phase 1: Backend (Foundation)
1. Create `/raw-data/*` endpoints
2. Implement table metadata endpoint
3. Support pagination (skip/limit)
4. Return structured responses

### Phase 2: Frontend (Main Page)
1. Create `RawDataViewerPage.tsx`
2. Add menu item to navigation
3. Implement table selection
4. Display data with pagination
5. Add export buttons

### Phase 3: Enhancements (Polish)
1. Add filtering component
2. Add column selector
3. Add sorting
4. Add advanced features

## Getting Started Checklist

- [ ] Read FRONTEND_ANALYSIS sections 1-4 (understand structure)
- [ ] Read FRONTEND_ANALYSIS sections 5-7 (understand patterns)
- [ ] Study QUICK_REFERENCE for common code patterns
- [ ] Start with RAW_DATA_VIEWER_IMPLEMENTATION Phase 1 (backend)
- [ ] Continue with Phase 2 (frontend)
- [ ] Test and add Phase 3 enhancements

## Important Notes

1. **Tab-Based Routing**: This is different from traditional React Router. All pages use state-based routing in App.tsx.

2. **API Client**: Always use `adminApiClient` from `/shared/admin-auth.ts` - it handles authentication automatically.

3. **Pagination**: Use server-side pagination (skip/limit) for production datasets, not client-side.

4. **Data Formatting**: Use `dayjs` for dates, `toLocaleString()` for numbers, tags for status values.

5. **Error Handling**: Always wrap API calls in try-catch, show messages to users.

6. **Loading States**: Always show loading spinners during async operations.

7. **TypeScript**: Define interfaces for all data structures, use strong typing.

## File Locations (Absolute Paths)

```
/Users/peakom/work/stock-analysis-system/
├── FRONTEND_ANALYSIS.md (this doc set)
├── FRONTEND_QUICK_REFERENCE.md
├── RAW_DATA_VIEWER_IMPLEMENTATION.md
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── components/
│       │   ├── AdminLayout.tsx
│       │   ├── StockListPage.tsx
│       │   └── [other pages]
│       ├── contexts/AuthContext.tsx
│       └── api/endpoints.ts
├── shared/admin-auth.ts
└── backend/app/models/
    └── daily_trading.py
```

## Next Steps

1. **Understand Current Architecture**: Read FRONTEND_ANALYSIS thoroughly
2. **Learn Patterns**: Study existing pages (StockListPage, ConceptAnalysisPage)
3. **Plan Your Page**: Use recommendations from FRONTEND_ANALYSIS section 7
4. **Build Incrementally**: Follow IMPLEMENTATION guide phases
5. **Use Quick Reference**: Copy code snippets as needed
6. **Test Thoroughly**: Check checklist before deploying

## Additional Resources

- Ant Design docs: https://ant.design/components/overview/
- React docs: https://react.dev/
- TypeScript docs: https://www.typescriptlang.org/docs/
- Axios docs: https://axios-http.com/docs/intro
- dayjs docs: https://day.js.org/

---

**Created**: November 14, 2025
**Project**: Stock Analysis System
**Frontend Version**: React 18.2 + Vite 7.1 + TypeScript
