# Contributing to DermaCare

Guidelines for developers and contributors to maintain code quality and project standards.

## Code Standards

### Python (Backend)

**Type Hints**

```python
from typing import Dict, Any, Optional, List
from PIL import Image

def process_image(
    image: Image.Image,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process image for analysis."""
    pass
```

**Docstrings**

```python
def predict_image(image: Image.Image) -> Dict[str, Any]:
    """
    Predict skin condition from image.

    Args:
        image: PIL Image object in RGB mode

    Returns:
        Dict with 'class_id' and 'confidence'

    Raises:
        ValueError: If image is invalid

    Example:
        >>> result = predict_image(img)
        >>> print(result['class_id'])
    """
    pass
```

**Logging**

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = process()
    logger.info(f"Processing successful: {result}")
except Exception as e:
    logger.error(f"Processing failed: {e}", exc_info=True)
```

### TypeScript/React (Frontend)

**Type Definitions**

```typescript
type AnalysisResult = {
  class_id: string;
  confidence: number;
  name: string;
  description: string;
};

interface ApiResponse {
  status: 'success' | 'error';
  data?: AnalysisResult;
  error?: string;
}
```

**Component Structure**

```typescript
export default function AnalysisComponent() {
  const [state, setState] = useState<StateType>(initialValue);

  const handleAnalyze = useCallback(() => {
    // Handler logic
  }, [dependencies]);

  return (
    // JSX
  );
}
```

## Development Workflow

### Setting Up Your Environment

```bash
# Clone repository
git clone <repo>
cd Derma-Care

# Setup backend
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Setup frontend
cd frontend
npm install
```

### Making Changes

1. **Create feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes with proper documentation**

3. **Test locally**

   ```bash
   # Backend
   python -m uvicorn backend.main:app --reload

   # Frontend
   cd frontend
   npm run dev
   ```

4. **Verify no errors**

   ```bash
   # Frontend linting
   npm run lint
   ```

5. **Commit with clear messages**

   ```bash
   git commit -m "feat: add new prediction algorithm"
   ```

### Commit Message Convention

```
feat: add new feature
fix: correct a bug
docs: update documentation
style: improve code formatting
refactor: restructure code without changing behavior
test: add or update tests
perf: improve performance
chore: update dependencies
```

## Code Review Checklist

- [ ] Code follows type hints convention
- [ ] All functions have docstrings
- [ ] Error handling is implemented
- [ ] Logging is appropriate
- [ ] No hardcoded secrets or paths
- [ ] No console.log or print in production code
- [ ] Tests pass locally
- [ ] No new dependencies without justification
- [ ] Documentation is updated

## API Development

### Adding New Endpoints

1. **Define in `backend/main.py`**

   ```python
   @app.post("/new-endpoint")
   async def new_endpoint(data: InputModel) -> OutputModel:
       """
       Endpoint description.

       Args:
           data: Input data

       Returns:
           Processed output
       """
       logger.info("Processing request")
       return {"status": "success"}
   ```

2. **Update documentation**
   - Add to README.md API reference
   - Add examples to SETUP.md

3. **Test with curl**

   ```bash
   curl -X POST http://localhost:8000/new-endpoint \
     -H "Content-Type: application/json" \
     -d '{"key": "value"}'
   ```

## Frontend Development

### Adding New Components

1. **Create component file**

   ```typescript
   // src/components/MyComponent.tsx
   export default function MyComponent() {
     return <div>Component</div>;
   }
   ```

2. **Use in page**

   ```typescript
   import MyComponent from '@/components/MyComponent';

   export default function Page() {
     return <MyComponent />;
   }
   ```

3. **Add types**

   ```typescript
   type Props = {
     title: string;
     onSubmit: (data: any) => void;
   };

   export default function MyComponent({ title, onSubmit }: Props) {
     // Component
   }
   ```

## Testing

### Backend Testing

```python
# test_api.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### Frontend Testing

```typescript
// __tests__/component.test.tsx
import { render, screen } from '@testing-library/react';
import MyComponent from '@/components/MyComponent';

test('renders component', () => {
  render(<MyComponent />);
  expect(screen.getByText('text')).toBeInTheDocument();
});
```

## Performance Optimization

### Backend

- Use GPU when available
- Implement caching for models
- Optimize image preprocessing
- Use batch processing for multiple images

### Frontend

- Use React.memo for expensive components
- Implement lazy loading
- Optimize images and assets
- Use CSS animations instead of JavaScript

## Security Guidelines

1. **Input Validation**

   ```python
   if not is_valid_image(file):
       raise HTTPException(status_code=400)
   ```

2. **Error Handling**
   - Never expose internal error details
   - Log detailed errors internally
   - Return generic messages publicly

3. **Secrets Management**

   ```python
   import os
   api_key = os.getenv('API_KEY', default='')
   ```

4. **CORS Configuration**

   ```python
   # Restrict to specific domains in production
   allow_origins=["https://yourdomain.com"]
   ```

## Documentation Requirements

### Every New Feature Should Include

1. **Code Comments**: Explain complex logic
2. **Docstrings**: All functions/classes
3. **README Updates**: If user-facing
4. **Examples**: In docstrings
5. **Type Hints**: All parameters and returns

## Dependency Management

### Adding New Packages

1. **Python**

   ```bash
   pip install package-name
   pip freeze > backend/requirements.txt
   ```

2. **Node.js**

   ```bash
   npm install package-name
   ```

3. **Justify in commit message**

   ```
   feat: add image optimization

   - Installs: pillow-simd==x.x.x for 3x faster image processing
   ```

## Release Process

1. **Update version** in files
2. **Update CHANGELOG**
3. **Run full test suite**
4. **Tag release** on git
5. **Build deployment packages**
6. **Document migration steps** if needed

## Debugging Tips

### Backend

```python
# Set debug logging
logging.basicConfig(level=logging.DEBUG)

# Print intermediate values
logger.debug(f"Value: {value}")

# Use pdb
import pdb; pdb.set_trace()
```

### Frontend

```javascript
// Console debugging
console.log('Value:', value);

// Browser DevTools
// F12 to open, Network tab for API calls

// React DevTools extension
// Helpful for component state inspection
```

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Import errors | Ensure Python path is set correctly |
| Port conflicts | Use different port with --port flag |
| Module not found | Install dependencies with pip install -r |
| Build errors | Clear .next and rebuild |
| CORS errors | Check backend CORS config |

## Questions & Support

- Check existing documentation first
- Search GitHub issues for similar problems
- Ask in project discussions/Slack
- Create detailed issue with reproduction steps

## Code of Conduct

- Be respectful to all contributors
- Focus on code, not the coder
- Ask before making major changes
- Review others' work thoroughly
- Share knowledge and help newer contributors

---

**Updated**: April 2026
**Maintainer**: DermaCare Team
