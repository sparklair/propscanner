;(() => {
	const MARKER = '1337'

	const report = (sink, ...values) => {
		if (values.some((value) => String(value).includes(MARKER))) {
			console.log(`[PP Gadget][${sink}]`, ...values)
		}
	}

	console.log('[PP] Hooks installed')

	const originalSetAttribute = Element.prototype.setAttribute
	Element.prototype.setAttribute = function (name, value) {
		report('setAttribute', name, value)
		return originalSetAttribute.call(this, name, value)
	}

	const originalInsertAdjacentHTML = Element.prototype.insertAdjacentHTML
	Element.prototype.insertAdjacentHTML = function (position, html) {
		report('insertAdjacentHTML', position, html)
		return originalInsertAdjacentHTML.call(this, position, html)
	}

	for (const sink of ['innerHTML', 'outerHTML']) {
		const descriptor = Object.getOwnPropertyDescriptor(Element.prototype, sink)

		if (!descriptor || !descriptor.set) continue

		Object.defineProperty(Element.prototype, sink, {
			configurable: descriptor.configurable,
			enumerable: descriptor.enumerable,
			get: descriptor.get,
			set(value) {
				report(sink, value)
				return descriptor.set.call(this, value)
			},
		})
	}

	const originalDocumentWrite = Document.prototype.write
	Document.prototype.write = function (...args) {
		report('document.write', ...args)
		return originalDocumentWrite.apply(this, args)
	}

	const originalEval = window.eval
	window.eval = function (code) {
		report('eval', code)
		return originalEval.call(this, code)
	}

	const originalFunction = window.Function
	window.Function = function (...args) {
		report('Function', ...args)
		return originalFunction.apply(this, args)
	}
	window.Function.prototype = originalFunction.prototype

	for (const timer of ['setTimeout', 'setInterval']) {
		const originalTimer = window[timer]
		window[timer] = function (handler, timeout, ...args) {
			report(timer, handler)
			return originalTimer.call(this, handler, timeout, ...args)
		}
	}

	const originalFetch = window.fetch
	window.fetch = function (input, init = {}) {
		const url = typeof input === 'string' ? input : input && input.url
		report('fetch', url, init && init.body)
		return originalFetch.call(this, input, init)
	}
})()
