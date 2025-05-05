// Terminal Manager Ultra-Optimizado
const Terminal = {
    init() {
        this.output = document.getElementById('terminal-output');
        this.input = document.getElementById('terminal-input');
        this.history = [];
        this.pos = -1;

        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this.execute();
            else if (e.key === 'ArrowUp') this.nav(-1);
            else if (e.key === 'ArrowDown') this.nav(1);
        });

        this.update();
        setInterval(() => this.update(), 1000);
    },

    async update() {
        try {
            const res = await fetch('/apps/terminal/output');
            const data = await res.json();
            this.output.innerHTML = this.formatOutput(data.output);
            this.output.scrollTop = this.output.scrollHeight;
        } catch (e) {
            console.error('Error updating terminal:', e);
        }
    },

    formatOutput(text) {
        return text.split('\n').map(line => {
            if (line.startsWith(">>> ")) {
                return `<span class="cmd">${line}</span>`;
            } else if (line.startsWith("Error:")) {
                return `<span class="err">${line}</span>`;
            }
            return `<span class="out">${line}</span>`;
        }).join('\n');
    },

    async execute() {
        const cmd = this.input.value.trim();
        if (!cmd) return;

        this.history.push(cmd);
        this.pos = this.history.length;

        try {
            await fetch('/apps/terminal/exec', {
                method: 'POST',
                body: cmd
            });
            this.input.value = '';
            this.update();
        } catch (e) {
            console.error('Execution error:', e);
        }
    },

    nav(dir) {
        if (!this.history.length) return;
        this.pos = Math.max(0, Math.min(this.history.length-1, this.pos + dir));
        this.input.value = this.history[this.pos] || '';
    }
};

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', () => Terminal.init());
