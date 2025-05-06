const Terminal = {
    init() {
        this.output = document.getElementById('terminal-output');
        this.input = document.getElementById('terminal-input');
        this.history = [];
        this.historyPos = -1;

        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.execute();
                e.preventDefault();
            } else if (e.key === 'ArrowUp') {
                this.navHistory(-1);
                e.preventDefault();
            } else if (e.key === 'ArrowDown') {
                this.navHistory(1);
                e.preventDefault();
            }
        });

        setInterval(() => this.updateOutput(), 1000);
    },

    async execute() {
        const command = this.input.value.trim();
        if (!command) return;
        
        this.history.push(command);
        this.historyPos = this.history.length;
        this.input.value = '';
        
        try {
            const response = await fetch('/terminal/exec', {
                method: 'POST',
                headers: {'Content-Type': 'text/plain'},
                body: command
            });
            
            const data = await response.json();
            this.displayOutput(data.output);
            
        } catch (error) {
            console.error('Error:', error);
            this.displayOutput(`Error: ${error.message}`);
        }
    },

    async updateOutput() {
        try {
            const response = await fetch('/terminal/output');
            const data = await response.json();
            this.displayOutput(data.output);
        } catch (error) {
            console.error('Update error:', error);
        }
    },

    displayOutput(text) {
        this.output.textContent = text;
        this.output.scrollTop = this.output.scrollHeight;
    },

    navHistory(direction) {
        if (!this.history.length) return;
        this.historyPos = Math.max(0, 
            Math.min(this.history.length - 1, this.historyPos + direction));
        this.input.value = this.history[this.historyPos] || '';
    }
};

document.addEventListener('DOMContentLoaded', () => Terminal.init());