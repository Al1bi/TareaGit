#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 14 16:07:50 2022

@author: usere
"""

from flask import Flask, render_template, request, redirect, url_for,session
from bson import ObjectId
from pymongo import MongoClient
from bson.son import SON
from datetime import datetime
import os

app = Flask(__name__)
categoriasDelPrograma=["Lacteos","Bebida","Cereales","Galleta"]
client = MongoClient("mongodb://localhost:27017")
db = client["MyPROYECTO"]
usuarios = db["Usuarios"]
productos=db["Productos"]
pedidos=db["Pedidos"]

carrito=db["Carrito"]

@app.route('/modoAdmin') 
def modoAdmin():
    productosSolicitadosTodos=list(db.Productos.find())
    return render_template('modoAdmin.html',productosRecibidosTodos=productosSolicitadosTodos)


@app.route('/') 
def inicio():
    productosSolicitadosTodos=list(db.Productos.find())
    pipeline=[{"$unwind":"$detallePedido"},{"$group":{"_id":{"idCliente":"$idUsuario","idProducto":"$detallePedido.idProducto"},"cantidadProductosPedidosPorUsuario":{"$sum":"$detallePedido.cantidad"}}},{"$match":{"_id.idCliente":ObjectId("637ad222cca958ea8f837c20")}},{"$sort":SON([("cantidadProductosPedidosPorUsuario",-1)])},{"$project":{"_idProductosFavs":"$_id.idProducto","_id":0}},{"$lookup":{"from":"Productos","localField":"_idProductosFavs","foreignField":"_id","as":"union"}},{"$unwind":"$union"},{"$project":{"_id":"$union._id","nombre":"$union.nombre","categoria":"$union.categoria","precio":"$union.precio","descripcion":"$union.descripcion"}}]
    productosSolicitadosMasComprados=list(db.Pedidos.aggregate(pipeline))
    pipeline2=[{"$unwind":"$detallePedido"},{"$group":{"_id":{"idProducto":"$detallePedido.idProducto"},"cantidadVecesPedido":{"$sum":"$detallePedido.cantidad"}}},{"$sort":SON([("cantidadVecesPedido",-1)])},{"$limit":9},{"$lookup":{"from":"Productos","localField":"_id.idProducto","foreignField":"_id","as":"union"}},{"$unwind":"$union"},{"$project":{"_id":"$union._id","nombre":"$union.nombre","categoria":"$union.categoria","precio":"$union.precio","descripcion":"$union.descripcion"}}]
    productosSolicitadosMasVendidos=list(db.Pedidos.aggregate(pipeline2))
    return render_template('index.html',categorias=categoriasDelPrograma,productosRecibidosTodos=productosSolicitadosTodos,productosMasComprados=productosSolicitadosMasComprados,productosMasVendidos=productosSolicitadosMasVendidos)


@app.route('/validarCuenta', methods=['POST'])
def validarCuenta():
    
    email = request.values.get("correo")
    contrasenia = request.values.get("contrasenia")
    
    resultado = usuarios.find( {"email":email, "contrasenia":contrasenia })
    
    if bool(resultado):
        #ir a la pagina principal pero con distinto parametro
        render_template('index.html')
    else:
        print("el correo y/o la contrasenia son incorrectos")

@app.route('/irLogin')
def irLogin():
    return render_template('login.html')

@app.route('/productosPorCategoria/<categoriaSolicitada>')
def productosPorCategoria(categoriaSolicitada):
    pipeline=[{"$match":{"categoria":categoriaSolicitada}}]
    productosSolicitados=list(db.Productos.aggregate(pipeline))
    return render_template('productosPorCategoria.html',productosRecibidos=productosSolicitados)


@app.route('/verDetalleDeProducto/<_idSolicitado>')
def verDetalleDeProducto(_idSolicitado):
     
    pipeline=[{"$match":{"_id":ObjectId(_idSolicitado)}}]
    productoSolicitado=(list(db.Productos.aggregate(pipeline)))[0]
    
    #consulta para ver si un producto ya fue agregado al carrito
    
    #idCliente = session['usuario']
    idCliente = "637ad222cca958ea8f837c1c"
    
    pipeline2 = [{"$unwind":"$productos"},{"$match":{"idCliente":ObjectId(idCliente),"productos.idProducto" :ObjectId(_idSolicitado)}}]
    enCarrito = len(list(db.Carrito.aggregate(pipeline2)))
    
    return render_template('verDetalleDeProducto.html',productoRecibido=productoSolicitado, estaEnCarrito=enCarrito )



@app.route('/success')
def success():
    return render_template('success.html')
@app.route('/irNuevaCuenta')
def irNuevaCuenta():
    return render_template('/nuevaCuenta.html')
#CATALOGO
@app.route('/crearProductoEnCatalogo')
def crearProductoEnCatalogo():
    return render_template('crearProductoEnCatalogo.html',categoriasRecibidas=categoriasDelPrograma)


@app.route('/registradorDeProductoEnCatalogo',methods = ['POST'])
def registradorDeProductoEnCatalogo():
    if request.method == 'POST':
        
        nombreP = request.form['np']
        categoriaP= request.form['cp']
        precioP= request.form['pp']
        descripcionP= request.form['dp']
        precioP=int(precioP)
        nuevo_producto={"nombre":nombreP,"categoria":categoriaP,"precio":precioP,"descripcion":descripcionP}
        x=productos.insert_one(nuevo_producto)
        print("Id:",x.inserted_id)
        return redirect(url_for('success'))
@app.route('/verCatalogoCompleto')
def verCatalogoCompleto():
    productosSolicitados=list(db.Productos.find())
    return render_template('productosPorCategoria.html',productosRecibidos=productosSolicitados)

@app.route('/modificarProductoDelCatalogo/<id>')
def modificarProductoDelCatalogo(id):
    productoSolicitadoModificar=list(db.Productos.find({"_id":ObjectId(id)}))[0]
    return render_template('modificarProducto.html',productoRecibidoModificar=productoSolicitadoModificar,categoriasRecibidas=categoriasDelPrograma)

@app.route('/modificadorDeProductoEnCatalogo',methods = ['POST'])
def modificadorDeProductoEnCatalogo():
    if request.method == 'POST':
        _idP=request.form['ip']
        nombreP = request.form['np']
        categoriaP= request.form['cp']
        precioP= request.form['pp']
        descripcionP= request.form['dp']
        precioP=int(precioP)
        productos.update_one({"_id":ObjectId(_idP)},{"$set":{"nombre":nombreP,"categoria":categoriaP,"precio":precioP,"descripcion":descripcionP}})
        return redirect(url_for('success'))

@app.route('/eliminadorProductoDelCatalogo/<id>')
def eliminadorProductoDelCatalogo(id):
    productos.delete_one({"_id":ObjectId(id)})
    return render_template('success.html')

#Desde aca viene mi modificacion
@app.route('/aniadirACarrito/<idP>/<precio>', methods = ['POST'])
def aniadirACarrito(idP, precio):
    if request.method == 'POST':
        
        #idCliente = session['usuario']
        idCliente = "637ad222cca958ea8f837c1c"
        
        cantidad = request.form['cant']
        subtotal =  float(cantidad)*float(precio)
        
        carrito.update_one({"idCliente":ObjectId(idCliente)},{ "$addToSet":{"productos": {"idProducto": ObjectId(idP), "cantidad":float(cantidad), "subtotal":float(subtotal)} } },True)
        
        return render_template('success.html')
        
    
@app.route('/eliminarDeCarrito/<idP>')
def eliminarDeCarrito(idP):
    #idCliente = session['usuario']
    idCliente = "637ad222cca958ea8f837c1c"
    
    pipeline = [{"$unwind":"$productos"},{"$match":{"idCliente":ObjectId(idCliente),"productos.idProducto":ObjectId(idP)}},{"$project":{"_id":False,"idProducto":"$productos.idProducto" ,"cantidad":"$productos.cantidad","subtotal":"$productos.subtotal"}}]
    obtenerParametros = (list(db.Carrito.aggregate(pipeline)))
    

    
    db.Carrito.update_one({"idCliente":ObjectId(idCliente)},{"$pull":{"productos": obtenerParametros[0] }})
    
    return render_template('success.html')

@app.route('/verCarrito')
def verCarrito():
    
    #idCliente = session['usuario']
    idCliente = "637ad222cca958ea8f837c1c" 
    
    pipeline=[{"$match":{"idCliente":ObjectId(idCliente)}},{"$unwind":"$productos"},{"$lookup":{"from": "Productos","localField": "productos.idProducto","foreignField": "_id", "as": "extension"}},{"$unwind":"$extension"},{"$project":{"_id":False,"idProducto":"$productos.idProducto","nombre":"$extension.nombre","categoria":"$extension.categoria","cantidad":"$productos.cantidad","subtotal":"$productos.subtotal"}}]
    
    productosEnCarrito=list(db.Carrito.aggregate(pipeline))
    
    #nuevo
    pipeline2=[{"$match":{"idCliente":ObjectId(idCliente)}},{"$unwind":"$productos"},{"$group":{"_id":"$idCliente","total":{"$sum":"$productos.subtotal"}}}]
    total = float(list(db.Carrito.aggregate(pipeline2))[0].get('total'))
    
    
    return render_template('carritoDeProductos.html', productosRecibidos=productosEnCarrito, totalAPagar=total)


@app.route('/vaciarCarrito')
def vaciarCarrito():
    """correoCliente = str(session['usuario'])
    consultaCliente = list(db.Usuarios.find({'email':correoCliente},{'_id':1}))
    idCliente = consultaCliente[0].get('_id')"""
    
    idCliente = "637ad222cca958ea8f837c1c" 
    
    db.Carrito.delete_one({"idCliente":ObjectId(idCliente)})
    return render_template('success.html')


@app.route('/checkOut/<total>')
def checkOut(total):
    
    """correoCliente = str(session['usuario'])
    consultaCliente = list(db.Usuarios.find({'email':correoCliente},{'_id':1}))
    idCliente = consultaCliente[0].get('_id')"""
    
    idCliente = "637ad222cca958ea8f837c1c" 
        
    pipeline=[{"$match":{"idCliente":ObjectId(idCliente)}},{"$lookup":{"from":"Usuarios","localField":"idCliente","foreignField":"_id","as": "extension" }},{"$unwind":"$extension"},{"$project":{"_id":False,"idCliente":True,"nombre":"$extension.nombre","apellido":"$extension.apellido","email":"$extension.email","celular":"$extension.celular","direccion":"$extension.direccion","productos":True}}]
    resumenDePedido = list(db.Carrito.aggregate(pipeline))[0]
    
    
    return render_template('checkOut.html', resumenPedido=resumenDePedido, total=total)


@app.route('/realizarPedido/<total>', methods=['POST'])
def realizarPedido(total):
    
    if request.method == 'POST':
        
        """correoCliente = str(session['usuario'])
        consultaCliente = list(db.Usuarios.find({'email':correoCliente},{'_id':1}))
        idCliente = consultaCliente[0].get('_id')"""
        
        idCliente = "637ad222cca958ea8f837c1c" 
    
        consultaProducto = list(db.Carrito.find({'idCliente': ObjectId(idCliente)}))

        fechaHora = datetime.now()
        nota = request.form['nt']
        tipoDePago = request.form['mp']
        detallePedido = consultaProducto[0].get('productos')
        montoTotal = float(total)
    
        db.Pedidos.insert_one({"idProducto":ObjectId(idCliente), "fechaHora":fechaHora, "nota":nota, "tipoDePago":tipoDePago, "detallePedido":detallePedido, "montoTotal":montoTotal })
        
        
        return render_template('success.html')

if __name__=='__main__':
    app.run(debug = False)

    