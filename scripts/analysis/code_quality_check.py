#!/usr/bin/env python3
"""
AI-Horizon Code Quality Checker

Comprehensive code quality analysis tool for the AI-Horizon project.
Checks for common issues, code style, documentation, and potential problems.
"""

import sys
import os
import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Set
from collections import defaultdict

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

class CodeQualityChecker:
    """Analyzes code quality across the AI-Horizon project."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.issues = defaultdict(list)
        self.stats = defaultdict(int)
        
    def check_all(self) -> Dict[str, Any]:
        """Run all quality checks and return results."""
        print("🔍 Running AI-Horizon Code Quality Analysis")
        print("=" * 50)
        
        python_files = list(self.project_root.rglob("*.py"))
        print(f"📁 Analyzing {len(python_files)} Python files...")
        
        for py_file in python_files:
            # Skip virtual environments and cache directories
            if any(part in str(py_file) for part in ['venv', '__pycache__', '.git', 'node_modules']):
                continue
            
            self._check_file(py_file)
        
        # Check project structure
        self._check_project_structure()
        
        # Check requirements.txt
        self._check_requirements()
        
        return self._generate_report()
    
    def _check_file(self, filepath: Path) -> None:
        """Check a single Python file for quality issues."""
        try:
            content = filepath.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            self.issues['encoding'].append(f"Cannot decode {filepath}: encoding issue")
            return
        
        self.stats['total_files'] += 1
        
        # Parse AST for deeper analysis
        try:
            tree = ast.parse(content)
            self._check_ast(tree, filepath)
        except SyntaxError as e:
            self.issues['syntax_errors'].append(f"{filepath}: {e}")
            return
        
        # Line-by-line checks
        lines = content.split('\n')
        self._check_lines(lines, filepath)
        
        # Documentation checks
        self._check_documentation(content, filepath)
        
        # Import checks
        self._check_imports(content, filepath)
    
    def _check_ast(self, tree: ast.AST, filepath: Path) -> None:
        """Check AST for structural issues."""
        for node in ast.walk(tree):
            # Check for overly complex functions
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                if complexity > 10:
                    self.issues['high_complexity'].append(
                        f"{filepath}:{node.lineno} - Function '{node.name}' has complexity {complexity}"
                    )
                
                # Check for missing docstrings in public functions
                if not node.name.startswith('_') and not ast.get_docstring(node):
                    self.issues['missing_docstrings'].append(
                        f"{filepath}:{node.lineno} - Function '{node.name}' missing docstring"
                    )
            
            # Check for overly long classes
            if isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    self.issues['missing_docstrings'].append(
                        f"{filepath}:{node.lineno} - Class '{node.name}' missing docstring"
                    )
    
    def _check_lines(self, lines: List[str], filepath: Path) -> None:
        """Check individual lines for issues."""
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Check for print statements (should use logging)
            if re.search(r'\bprint\s*\(', line) and 'test_' not in str(filepath):
                self.issues['print_statements'].append(f"{filepath}:{i} - Use logging instead of print()")
            
            # Check for TODO/FIXME comments
            if re.search(r'\b(TODO|FIXME|XXX|HACK)\b', line, re.IGNORECASE):
                self.issues['todo_comments'].append(f"{filepath}:{i} - {line_stripped}")
            
            # Check for overly long lines
            if len(line) > 120:
                self.issues['long_lines'].append(f"{filepath}:{i} - Line too long ({len(line)} chars)")
            
            # Check for debug/temp code
            if re.search(r'\b(debug|temp|temporary|TEMP|DEBUG)\b', line, re.IGNORECASE):
                if any(pattern in line.lower() for pattern in ['= true', '= false', 'breakpoint', 'pdb']):
                    self.issues['debug_code'].append(f"{filepath}:{i} - Potential debug code: {line_stripped}")
    
    def _check_documentation(self, content: str, filepath: Path) -> None:
        """Check documentation quality."""
        # Module-level docstring
        tree = ast.parse(content)
        module_docstring = ast.get_docstring(tree)
        
        if not module_docstring and not str(filepath).endswith('__init__.py'):
            self.issues['missing_module_docstring'].append(str(filepath))
        elif module_docstring and len(module_docstring.strip()) < 20:
            self.issues['short_module_docstring'].append(str(filepath))
    
    def _check_imports(self, content: str, filepath: Path) -> None:
        """Check import statements for issues."""
        lines = content.split('\n')
        imports = []
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if line_stripped.startswith(('import ', 'from ')):
                imports.append((i, line_stripped))
        
        # Check for wildcard imports
        for line_num, import_line in imports:
            if 'import *' in import_line:
                self.issues['wildcard_imports'].append(f"{filepath}:{line_num} - {import_line}")
    
    def _check_project_structure(self) -> None:
        """Check overall project structure."""
        required_files = [
            'requirements.txt',
            'README.md',
            '.env.example',
            'setup.py'
        ]
        
        for req_file in required_files:
            if not (self.project_root / req_file).exists():
                self.issues['missing_files'].append(f"Missing {req_file}")
        
        # Check directory structure
        required_dirs = ['aih', 'scripts', 'tests', 'docs', 'templates']
        for req_dir in required_dirs:
            if not (self.project_root / req_dir).is_dir():
                self.issues['missing_directories'].append(f"Missing directory: {req_dir}")
    
    def _check_requirements(self) -> None:
        """Check requirements.txt for issues."""
        req_file = self.project_root / 'requirements.txt'
        if not req_file.exists():
            return
        
        content = req_file.read_text()
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        
        packages = defaultdict(list)
        for line in lines:
            if '>=' in line:
                package = line.split('>=')[0].strip()
                packages[package].append(line)
        
        # Check for duplicates
        for package, versions in packages.items():
            if len(versions) > 1:
                self.issues['duplicate_requirements'].append(f"Duplicate package: {package} - {versions}")
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality report."""
        total_issues = sum(len(issues) for issues in self.issues.values())
        
        print(f"\n📊 CODE QUALITY REPORT")
        print("=" * 50)
        print(f"Files analyzed: {self.stats['total_files']}")
        print(f"Total issues found: {total_issues}")
        
        if total_issues == 0:
            print("🎉 No code quality issues found!")
            return {'status': 'excellent', 'issues': {}, 'stats': dict(self.stats)}
        
        # Sort issues by severity
        severity_order = [
            'syntax_errors', 'encoding', 'wildcard_imports', 'missing_files',
            'missing_directories', 'duplicate_requirements', 'high_complexity',
            'debug_code', 'print_statements', 'missing_docstrings',
            'missing_module_docstring', 'todo_comments', 'long_lines'
        ]
        
        for category in severity_order:
            if category in self.issues:
                issues = self.issues[category]
                print(f"\n⚠️  {category.upper().replace('_', ' ')} ({len(issues)} issues):")
                for issue in issues[:5]:  # Show first 5 issues
                    print(f"   - {issue}")
                if len(issues) > 5:
                    print(f"   ... and {len(issues) - 5} more")
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"   • {rec}")
        
        return {
            'status': 'needs_improvement' if total_issues > 20 else 'good',
            'issues': dict(self.issues),
            'stats': dict(self.stats),
            'recommendations': recommendations
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on found issues."""
        recommendations = []
        
        if 'print_statements' in self.issues:
            recommendations.append("Replace print() statements with proper logging using the logging module")
        
        if 'missing_docstrings' in self.issues:
            recommendations.append("Add docstrings to public functions and classes for better documentation")
        
        if 'high_complexity' in self.issues:
            recommendations.append("Refactor complex functions into smaller, more manageable pieces")
        
        if 'todo_comments' in self.issues:
            recommendations.append("Address TODO comments or create issues to track them")
        
        if 'duplicate_requirements' in self.issues:
            recommendations.append("Clean up requirements.txt to remove duplicate dependencies")
        
        return recommendations

def main():
    """Main entry point for code quality checker."""
    checker = CodeQualityChecker()
    results = checker.check_all()
    
    # Exit with appropriate code
    if results['status'] == 'excellent':
        sys.exit(0)
    elif results['status'] == 'good':
        sys.exit(0)
    else:
        print("\n❌ Code quality needs improvement. Please address the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 