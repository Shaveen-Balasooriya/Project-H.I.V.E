/**
 * Banner Validation Module
 * 
 * Validates and sanitizes honeypot banner messages according to security constraints
 */

class BannerValidator {
  // Constants for validation rules
  static CONSTRAINTS = {
    MAX_LINE_LENGTH: 100,    // Maximum 100 characters per line
    MAX_LINES: 4,           // Maximum 4 lines
    MIN_TOTAL_LENGTH: 10    // Minimum 10 non-whitespace characters
  };
  
  // Define disallowed characters for easy reference
  static DISALLOWED_CHARS = {
    '\\': 'Backslash (\\)',
    '`': 'Backtick (`)',
    '"': 'Double quote (")',
    "'": 'Single quote (\')',
    ';': 'Semicolon (;)',
    '&': 'Ampersand (&)',
    '$': 'Dollar sign ($)'
  };
  
  /**
   * Validates a banner string against all constraints
   * @param {string} banner - The banner text to validate
   * @returns {Object} Result with isValid flag and optional error message
   */
  static validate(banner) {
    if (!banner) {
      return {
        isValid: false,
        message: "Banner cannot be empty"
      };
    }
    
    const disallowedCharsResult = this.checkDisallowedCharacters(banner);
    if (!disallowedCharsResult.isValid) {
      return disallowedCharsResult;
    }
    
    const lines = banner.split('\n');
    if (lines.length > this.CONSTRAINTS.MAX_LINES) {
      return {
        isValid: false,
        message: `Banner cannot exceed ${this.CONSTRAINTS.MAX_LINES} lines (currently has ${lines.length})`
      };
    }
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (line.length > this.CONSTRAINTS.MAX_LINE_LENGTH) {
        return {
          isValid: false,
          message: `Line ${i + 1} exceeds the maximum length of ${this.CONSTRAINTS.MAX_LINE_LENGTH} characters`
        };
      }
    }
    
    const nonWhitespaceLength = banner.replace(/\s/g, '').length;
    if (nonWhitespaceLength < this.CONSTRAINTS.MIN_TOTAL_LENGTH) {
      return {
        isValid: false,
        message: `Banner must contain at least ${this.CONSTRAINTS.MIN_TOTAL_LENGTH} non-whitespace characters`
      };
    }
    
    return { isValid: true };
  }
  
  /**
   * Checks banner for disallowed characters
   * @param {string} banner - Banner text to check
   * @returns {Object} Result with isValid flag and optional error message
   */
  static checkDisallowedCharacters(banner) {
    const controlCharRegex = /[\x00-\x08\x0B\x0C\x0E-\x1F]/;
    if (controlCharRegex.test(banner)) {
      return {
        isValid: false,
        message: "Banner contains disallowed control characters"
      };
    }
    
    for (const [char, name] of Object.entries(this.DISALLOWED_CHARS)) {
      if (banner.includes(char)) {
        return {
          isValid: false,
          message: `Banner contains disallowed character: ${name}`
        };
      }
    }
    
    return { isValid: true };
  }
  
  /**
   * Sanitizes banner by removing disallowed characters
   * @param {string} banner - Banner text to sanitize
   * @returns {string} Sanitized banner text
   */
  static sanitize(banner) {
    if (!banner) return '';
    
    let sanitized = banner
      .replace(/[\\`"';$]/g, '')
      .replace(/&/g, '+');
    
    sanitized = sanitized.replace(/[\x00-\x09\x0B\x0C\x0E-\x1F]/g, '');
    
    const lines = sanitized.split('\n');
    const truncatedLines = lines.slice(0, this.CONSTRAINTS.MAX_LINES);
    
    const processedLines = truncatedLines.map(line => 
      line.substring(0, this.CONSTRAINTS.MAX_LINE_LENGTH)
    );
    
    return processedLines.join('\n');
  }
  
  /**
   * Gets the regex pattern to match all disallowed characters
   * @returns {RegExp} Regex pattern for disallowed characters
   */
  static getDisallowedCharsPattern() {
    const specialChars = Object.keys(this.DISALLOWED_CHARS).join('');
    return new RegExp(`[${specialChars}]|[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F]`);
  }
  
  /**
   * Gets statistics about a banner text
   * @param {string} banner - Banner text to analyze
   * @returns {Object} Banner statistics
   */
  static getStats(banner) {
    if (!banner) return { lines: 0, chars: 0, nonWhitespace: 0 };
    
    const lines = banner.split('\n');
    const chars = banner.length;
    const nonWhitespace = banner.replace(/\s/g, '').length;
    
    return {
      lines: lines.length,
      chars: chars,
      nonWhitespace: nonWhitespace,
      lineDetails: lines.map((line, i) => ({
        number: i + 1,
        length: line.length,
        content: line
      }))
    };
  }
  
  /**
   * Sets up event listeners to prevent typing disallowed characters
   * and enforce line/character limits in real-time
   * @param {HTMLTextAreaElement} textarea - The banner textarea element
   */
  static setupPreventDisallowedChars(textarea) {
    if (!textarea) return;
    
    const disallowedPattern = this.getDisallowedCharsPattern();
    
    textarea.addEventListener('keypress', (e) => {
      if (e.key === 'Tab' || e.key === 'Backspace') {
        return true;
      }
      
      const char = String.fromCharCode(e.charCode);
      
      if (e.key === 'Enter') {
        const lines = textarea.value.split('\n');
        if (lines.length >= this.CONSTRAINTS.MAX_LINES) {
          e.preventDefault();
          return false;
        }
        return true;
      }
      
      if (disallowedPattern.test(char)) {
        e.preventDefault();
        return false;
      }
      
      const cursorPosition = textarea.selectionStart;
      const textBeforeCursor = textarea.value.substring(0, cursorPosition);
      const textAfterCursor = textarea.value.substring(cursorPosition);
      
      const linesBeforeCursor = textBeforeCursor.split('\n');
      const currentLine = linesBeforeCursor[linesBeforeCursor.length - 1];
      
      if (currentLine.length >= this.CONSTRAINTS.MAX_LINE_LENGTH && 
          textarea.selectionStart === textarea.selectionEnd) {
        e.preventDefault();
        return false;
      }
    });
    
    textarea.addEventListener('input', (e) => {
      const text = textarea.value;
      const lines = text.split('\n');
      
      if (lines.length > this.CONSTRAINTS.MAX_LINES) {
        textarea.value = lines.slice(0, this.CONSTRAINTS.MAX_LINES).join('\n');
      }
      
      let modified = false;
      const truncatedLines = lines.map((line, i) => {
        if (i < this.CONSTRAINTS.MAX_LINES && line.length > this.CONSTRAINTS.MAX_LINE_LENGTH) {
          modified = true;
          return line.substring(0, this.CONSTRAINTS.MAX_LINE_LENGTH);
        }
        return i < this.CONSTRAINTS.MAX_LINES ? line : '';
      });
      
      if (modified) {
        const cursorPos = textarea.selectionStart;
        textarea.value = truncatedLines.join('\n');
        textarea.setSelectionRange(Math.min(cursorPos, textarea.value.length), 
                                Math.min(cursorPos, textarea.value.length));
      }
      
      const sanitized = this.sanitize(textarea.value);
      if (sanitized !== textarea.value) {
        const cursorPos = textarea.selectionStart;
        textarea.value = sanitized;
        textarea.setSelectionRange(Math.min(cursorPos, textarea.value.length), 
                                Math.min(cursorPos, textarea.value.length));
      }
    });
    
    textarea.addEventListener('paste', (e) => {
      e.preventDefault();
      
      let text = (e.clipboardData || window.clipboardData).getData('text');
      
      const lines = text.split('\n');
      
      const existingText = textarea.value;
      const cursorPos = textarea.selectionStart;
      const existingLines = existingText.split('\n');
      let currentLineIndex = 0;
      let charCountBeforeCursor = 0;
      
      for (let i = 0; i < existingLines.length; i++) {
        if (charCountBeforeCursor + existingLines[i].length >= cursorPos) {
          currentLineIndex = i;
          break;
        }
        charCountBeforeCursor += existingLines[i].length + 1;
      }
      
      const currentLine = existingLines[currentLineIndex] || "";
      const currentLinePos = cursorPos - charCountBeforeCursor;
      const remainingSpaceInLine = this.CONSTRAINTS.MAX_LINE_LENGTH - currentLine.length;
      
      const availableLines = this.CONSTRAINTS.MAX_LINES - existingLines.length + 1;
      
      const processedLines = [];
      if (availableLines > 0) {
        if (lines.length > 0) {
          const firstLine = lines[0].substring(0, remainingSpaceInLine);
          processedLines.push(firstLine);
        }
        
        for (let i = 1; i < Math.min(lines.length, availableLines); i++) {
          processedLines.push(lines[i].substring(0, this.CONSTRAINTS.MAX_LINE_LENGTH));
        }
      }
      
      text = processedLines.join('\n');
      
      text = this.sanitize(text);
      
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const value = textarea.value;
      
      textarea.value = value.substring(0, start) + text + value.substring(end);
      textarea.selectionStart = textarea.selectionEnd = start + text.length;
    });
  }
  
  /**
   * Updates banner validation UI
   * @param {HTMLTextAreaElement} textarea - The banner textarea element
   * @param {HTMLElement} errorContainer - Element to show errors in
   * @param {HTMLElement} statsContainer - Optional element to show stats in
   * @returns {boolean} Whether the banner is valid
   */
  static updateValidationUI(textarea, errorContainer, statsContainer = null) {
    if (!textarea || !errorContainer) return false;
    
    const banner = textarea.value;
    const result = this.validate(banner);
    const stats = this.getStats(banner);
    
    if (!result.isValid) {
      HoneypotFormValidator.setInvalid(textarea, true);
      errorContainer.textContent = result.message;
      errorContainer.classList.remove('hidden');
    } else {
      HoneypotFormValidator.setInvalid(textarea, false);
      errorContainer.classList.add('hidden');
    }
    
    if (statsContainer) {
      statsContainer.textContent = `${stats.lines}/${this.CONSTRAINTS.MAX_LINES} lines, ${stats.nonWhitespace}/${this.CONSTRAINTS.MIN_TOTAL_LENGTH}+ chars`;
      
      if (stats.lines >= this.CONSTRAINTS.MAX_LINES * 0.75 || 
          stats.nonWhitespace <= this.CONSTRAINTS.MIN_TOTAL_LENGTH * 1.2) {
        statsContainer.classList.add('text-warning');
      } else {
        statsContainer.classList.remove('text-warning');
      }
    }
    
    return result.isValid;
  }
}

// Export for module usage
window.BannerValidator = BannerValidator;
