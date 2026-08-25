<?php

namespace SecureWare\Core;

class Router
{
    /** @var array<int, array{method:string, regex:string, params:array, handler:mixed}> */
    private array $routes = [];

    public function get(string $pattern, mixed $handler): void
    {
        $this->add('GET', $pattern, $handler);
    }

    public function post(string $pattern, mixed $handler): void
    {
        $this->add('POST', $pattern, $handler);
    }

    public function any(string $pattern, mixed $handler): void
    {
        $this->add('GET', $pattern, $handler);
        $this->add('POST', $pattern, $handler);
    }

    private function add(string $method, string $pattern, mixed $handler): void
    {
        $paramNames = [];
        $regex = preg_replace_callback('#\{([a-zA-Z_][a-zA-Z0-9_]*)\}#', function ($m) use (&$paramNames) {
            $paramNames[] = $m[1];
            return '([^/]+)';
        }, rtrim($pattern, '/'));

        $regex = '#^' . ($regex === '' ? '/' : $regex) . '$#';

        $this->routes[] = [
            'method'  => $method,
            'regex'   => $regex,
            'params'  => $paramNames,
            'handler' => $handler,
        ];
    }

    public function dispatch(Request $request): void
    {
        foreach ($this->routes as $route) {
            if ($route['method'] !== $request->method) {
                continue;
            }

            if (!preg_match($route['regex'], $request->path, $matches)) {
                continue;
            }

            array_shift($matches);
            $params = array_combine($route['params'], $matches);
            $request->params = $params;

            $this->call($route['handler'], $request, $params);
            return;
        }

        Response::notFound();
    }

    private function call(mixed $handler, Request $request, array $params): void
    {
        if ($handler instanceof \Closure) {
            call_user_func($handler, $request, ...array_values($params));
            return;
        }

        [$class, $method] = $handler;
        $controller = new $class();
        call_user_func([$controller, $method], $request, ...array_values($params));
    }
}
