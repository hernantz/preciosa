from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import Q
import operator

from rest_framework import viewsets, mixins, generics

from cities_light.models import City
from preciosa.precios.models import (Sucursal, Cadena, Producto,
                                     EmpresaFabricante, Marca, Categoria)

from preciosa.precios.serializers import (CadenaSerializer, SucursalSerializer,
                                          CitySerializer, ProductoSerializer,
                                          EmpresaFabricanteSerializer, MarcaSerializer,
                                          CategoriaSerializer)


class CreateListRetrieveViewSet(mixins.CreateModelMixin,
                                mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    """
    A viewset that provides `retrieve`, `create`, and `list` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.filter(country__name='Argentina')
    serializer_class = CitySerializer


class CadenaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Cadena.objects.all()
    serializer_class = CadenaSerializer


class EmpresaFabricanteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EmpresaFabricante.objects.all()
    serializer_class = EmpresaFabricanteSerializer


class MarcaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer


class CategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class SucursalesList(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     generics.GenericAPIView):

    queryset = Sucursal.objects.all()
    serializer_class = SucursalSerializer

    def get_queryset(self):
        queryset = super(SucursalesList, self).get_queryset()

        q = self.request.QUERY_PARAMS.get('q', None)
        limit = self.request.QUERY_PARAMS.get('limit', None)

        lat = self.request.QUERY_PARAMS.get('lat', None)
        lon = self.request.QUERY_PARAMS.get('lon', None)
        radio = self.request.QUERY_PARAMS.get('radio', None)

        if q:
            words = q.split(' ')
            queryset = queryset.filter(Q(cadena__nombre__icontains=q) | Q(nombre__icontains=q))

        if all((lat, lon, radio)):
            try:
                lat = float(lat)
                lon = float(lon)
                radio = float(radio)

            except ValueError:
                pass

            else:
                point = Point(lon, lat, srid=4326)
                circulo = (point, D(km=radio))
                queryset = queryset.filter(ubicacion__distance_lte=circulo)
                queryset = queryset.distance(point).order_by('distance')

        if limit:
            queryset = queryset[:limit]

        return queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ProductosList(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     generics.GenericAPIView):

    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

    def get_queryset(self):
        queryset = super(ProductosList, self).get_queryset()
        barcode = self.request.QUERY_PARAMS.get('barcode', None)
        q = self.request.QUERY_PARAMS.get('q', None)

        if barcode:
            queryset = queryset.filter(upc__icontains=barcode)

        if q:
            words = q.split(' ')
            queryset = queryset.filter(
                Q(reduce(operator.and_, (Q(descripcion__icontains=w) for w in words)))
                #| Q(marca__nombre__icontains=q)
                #| Q(marca__fabricante__nombre__icontains=q)
            )

        return queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
