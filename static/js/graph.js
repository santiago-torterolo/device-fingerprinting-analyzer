/*
Device Fingerprinting Network Graph - Interactive D3.js Visualization
Supports: zoom, pan, drag nodes, hover tooltips, risk coloring
*/

let simulation, svg, width, height, nodeElements, linkElements;

// Initialize graph on page load
document.addEventListener('DOMContentLoaded', function() {
    loadGraphData();
});

function loadGraphData() {
    const loading = document.getElementById('loading');
    if (loading) loading.style.display = 'block';
    
    fetch('/api/graph-data?limit=150')
        .then(response => response.json())
        .then(data => renderGraph(data))
        .catch(error => {
            console.error('Graph data error:', error);
            if (loading) {
                loading.innerHTML = '<p class="text-danger mt-2">Failed to load graph data</p>';
            }
        });
}

function renderGraph(data) {
    const container = document.getElementById('graph-container');
    const loading = document.getElementById('loading');
    if (loading) loading.style.display = 'none';

    width = container.clientWidth;
    height = 700;
    
    d3.select(container).select('svg').remove();
    
    svg = d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .style('background', '#1a1d21'); // Darker premium background
    
    const g = svg.append('g');
    
    // Zoom behavior
    const zoom = d3.zoom()
        .scaleExtent([0.1, 8])
        .on('zoom', (event) => g.attr('transform', event.transform));
    
    svg.call(zoom);
    
    // Improved Force simulation for a more compact view
    simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.links).id(d => d.id).distance(45)) // Shorter links
        .force('charge', d3.forceManyBody().strength(-150)) // Less repulsion
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('x', d3.forceX(width / 2).strength(0.08)) // Horizontal gravity
        .force('y', d3.forceY(height / 2).strength(0.08)) // Vertical gravity
        .force('collision', d3.forceCollide(30));
    
    // Gradient for links
    const defs = svg.append('defs');
    
    // Links with better visibility
    linkElements = g.append('g')
        .selectAll('.link')
        .data(data.links)
        .enter().append('line')
        .classed('link', true)
        .attr('stroke-width', d => d.risk_flag === 'high' ? 3 : 1.5)
        .attr('stroke', d => {
            if (d.risk_flag === 'high') return '#ff4d4d';
            if (d.risk_flag === 'medium') return '#ffa500';
            return '#4a4e54';
        })
        .attr('opacity', 0.6);
    
    // Nodes with Glow effects and distinct styling
    nodeElements = g.append('g')
        .selectAll('.node')
        .data(data.nodes)
        .enter().append('g')
        .classed('node', true)
        .call(drag(simulation));
        
    // Node Shadow/Glow
    nodeElements.append('circle')
        .attr('r', d => d.group === 'account' ? 14 : 18)
        .attr('fill', d => {
            if (d.group === 'account') return '#00d2ff';
            const score = d.risk_score || 0;
            if (score > 70) return '#ff4d4d'; // Red alert
            if (score > 40) return '#ffcc00'; // Warning
            return '#00ff88'; // Clean
        })
        .style('filter', 'drop-shadow(0px 0px 5px rgba(0,0,0,0.5))')
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);
    
    // Icon or Initial in the middle
    nodeElements.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '.35em')
        .attr('font-family', 'FontAwesome')
        .attr('font-size', d => d.group === 'account' ? '10px' : '12px')
        .attr('fill', '#fff')
        .attr('pointer-events', 'none')
        .text(d => d.group === 'account' ? '\uf007' : '\uf109'); // User icon vs Laptop icon
    
    // Labels below nodes with better contrast
    nodeElements.append('text')
        .attr('dy', d => d.group === 'account' ? 25 : 30)
        .attr('text-anchor', 'middle')
        .attr('font-size', '11px')
        .attr('font-weight', 'bold')
        .attr('fill', '#e0e0e0')
        .attr('pointer-events', 'none')
        .text(d => (d.label || d.id).substring(0, 18));
    
    // Tooltips
    nodeElements.append('title')
        .text(d => `${d.group.toUpperCase()}\nStatus: ${d.risk_score || 0}\nID: ${d.id}`);
    
    simulation.on('tick', () => {
        linkElements
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        nodeElements
            .attr('transform', d => `translate(${d.x}, ${d.y})`);
    });
}

// Drag functions
function drag(simulation) {
    function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }
    
    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }
    
    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
    }
    
    return d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended);
}

// Button handlers
document.addEventListener('DOMContentLoaded', function() {
    const resetBtn = document.getElementById('reset-btn');
    const refreshBtn = document.getElementById('refresh-graph');
    
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            svg.transition().duration(750)
                .call(d3.zoom().transform, d3.zoomIdentity);
        });
    }
    
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadGraphData);
    }
});

// Responsive resize
window.addEventListener('resize', () => {
    if (svg) {
        width = document.getElementById('graph-container').clientWidth;
        svg.attr('width', width);
        if (simulation) {
            simulation.force('center', d3.forceCenter(width / 2, height / 2));
        }
    }
});
