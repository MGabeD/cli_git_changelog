
---

#  CLI Git Changelog Generator

This tool provides a simple CLI interface to automatically generate human-readable changelogs based on your Git commit history.

##  What It Does

Given a repository, this tool extracts Git commit data and generates detailed changelogs using an LLM model. It can summarize:

-  File-level changes for each individual commit
-  Combined summaries for batches of commits

This is especially useful for:
- Release notes
- PR summaries
- Understanding codebase evolution
- Keeping non-technical stakeholders in the loop

##  Features

- **Automatic Diff Analysis**: Pulls Git diffs for each commit and converts them into high-level changelogs.
- **Batch Generating Changelogs**: Summarize changes across multiple commits in one go by setting -n to a number greater than 1.
- **File-by-File Prompts**: Generates prompts for each changed file to improve clarity and traceability.
- **Model-Backed Generation**: Uses an LLM to interpret changes in plain English.

##  Installation

```bash
pip install -e .
```
Or you can do this if you want to add it into one of your projects

```bash
pip install git+https://github.com/MGabeD/cli_git_changelog.git
```

If you prefer not to pass everything via CLI arguements, you can use a .env file. Make sure your `API_KEY` and other relevant environment variables are set up via a `.env` file. In the directory you run this from, or export them yourself and the program will grab them. 

##  Usage

```bash
generate-changelog --n 5
```

Options:
- Run with generate-changelog -h to get all of the options for the CLI tool

##  Example Output

<details>
  <summary>A Real Output from the tool going over 2 commits</summary>

  # Candidate Filtering System Update

This release introduces significant improvements to our candidate filtering system, enhancing data type handling and comparison capabilities.

### Major Improvements
- Added support for boolean string comparisons ("true"/"false")
- Implemented datetime ISO format string handling
- Enhanced numeric comparison with automatic float conversion
- Added result inversion capability for all filter types

### Technical Details
- **Boolean Handling**: New boolean parsing system that handles both string ("true"/"false") and native boolean values
- **DateTime Support**: Added ISO format datetime string support with comparison operators (eq, gt, lt)
- **Numeric Processing**: Improved numeric comparison with automatic type conversion and validation
- **Filter Inversion**: New `invert` parameter allowing for inverse filtering across all filter types

### Documentation
- Added comprehensive code examples for each filter type
- Updated function documentation with type specifications
- Included error handling recommendations
- Added testing guidelines for all new features

### Error Handling
- Enhanced type validation for filter inputs
- Added operator validation system
- Improved error messaging for invalid inputs

This update significantly improves the flexibility and reliability of the candidate filtering system while maintaining strict type safety and validation.

</details>

##  Notes

- The tool depends on a running model API (e.g., Claude, GPT) to generate changelog content.
- Requires Python 3.10.

---