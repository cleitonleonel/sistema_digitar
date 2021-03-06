# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import datetime
from decimal import Decimal

from django.db import models
from modules.entidade.models import entidade

from modules.entidade.formularios import MENSAGENS_ERROS
from modules.servico.models import Plano


class Contrato(models.Model):
    plano = models.ForeignKey(Plano, default=1)

    cliente = models.ForeignKey(entidade, default=1)
    opcoes_tipos_clientes = (('PF', 'PESSOA FISICA'), ('PJ', 'PESSOA JURIDICA'),)
    tipo_cliente  = models.CharField("Tipo do Cliente:",max_length=2,null=False,default='PJ',choices = opcoes_tipos_clientes,error_messages=MENSAGENS_ERROS)

    vigencia_inicio = models.DateField(null=True)
    vigencia_fim    = models.DateField(null=True)

    taxa_honorario  = models.DecimalField("Honorário:", max_digits=5, decimal_places=2, null=True,blank=False)
    valor_honorario = models.DecimalField("Valor:", max_digits=6, decimal_places=2, null=True,blank=False)
    valor_total = models.DecimalField("Total:", max_digits=8, decimal_places=2, null=True, blank=False)
    dia_vencimento  = models.CharField("Dia do Vencimento",null=True,default=5,max_length=2)
    data_vencimento = models.DateField("Data de Vencimento",null=True)

    desconto_temporario = models.DecimalField("Desconto Temporário:", max_digits=5,default=0, decimal_places=2, null=True,blank=True)
    desconto_temporario_ativo  = models.DecimalField("Desconto Temporário Ativo:", max_digits=5,default=0, decimal_places=2, null=True,blank=True)
    desconto_inicio = models.DateField(null=True)
    desconto_fim    = models.DateField(null=True)

    desconto_indicacoes = models.DecimalField("Desconto por Indicações:", max_digits=5, decimal_places=2, default=0, null=True,blank=True)
    servicos_contratados = models.CharField("Serviços:",null=True,max_length=100)
    cadastrado_por = models.ForeignKey(entidade,  related_name = "cadastrado_por",default=1)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    ultima_alteracao = models.DateTimeField(null=True, auto_now=True)
    alterado_por = models.ForeignKey(entidade, related_name = "alterado_por",default=1)
    ativo = models.BooleanField(default=True)

    def serialize(self):
        serialized_values = {}

    def totalizar_honorario(self):
        desconto_temporario = self.calcular_desconto_temporario()
        desconto_fidelidade = self.calcular_desconto_fidelidade()
        self.desconto_temporario_ativo = desconto_temporario
        self.desconto_indicacoes = desconto_fidelidade
        desconto_total = Decimal(desconto_temporario)/100 + Decimal(desconto_fidelidade)/100
        self.valor_total = Decimal(self.valor_honorario)*(1-desconto_total)
        self.save()
        #print('HONORARIO: ',self.valor_honorario,' - DESC.TEMP.:',desconto_temporario,' - DESC.FID.:',desconto_fidelidade,' - DESC.TOTAL: ',desconto_total,' - TOTAL: ',self.valor_total)


    def calcular_desconto_temporario(self):
        if self.desconto_temporario is not None:
            if self.verificar_validade_desconto_temporario(self.desconto_inicio,self.desconto_fim):
                desconto = self.desconto_temporario
                return Decimal(desconto)
        return Decimal(0)

    def verificar_validade_desconto_temporario(self,inicio=None,termino=None):
        current_date = datetime.datetime.now().date()
        if inicio is not None:
            if current_date < inicio:
                return False

        if termino is not None:
            if current_date > termino:
                return False
        return True

    def calcular_desconto_fidelidade(self):
        indicacoes = Indicacao.objects.filter(cliente=self.cliente).filter(indicacao_ativa=True)
        print("VEJA QUANTAS INDICACOES ATIVAS TEMOS: ",indicacoes)
        if len(indicacoes) == 0:
            return Decimal(0)
        else:
            desconto = Decimal(0)
            for item in indicacoes:
                print(item.indicacao.nome_razao,item.indicacao.ativo,item.taxa_desconto)
                if item.indicacao.ativo:
                    desconto = desconto + item.taxa_desconto
            return desconto


class Indicacao (models.Model):
    cliente = models.ForeignKey(entidade, related_name = "cliente")
    indicacao = models.ForeignKey(entidade,related_name = "indicacao")
    taxa_desconto = models.DecimalField("Taxa Desconto",max_digits=5, decimal_places=2, default=0)
    indicacao_ativa = models.BooleanField(default=True)
    cadastrado_por = models.ForeignKey(entidade, related_name="indicacao_cadastrado_por", default=1)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    ultima_alteracao = models.DateTimeField(null=True, auto_now=True)
    alterado_por = models.ForeignKey(entidade, related_name="indicacao_alterado_por", default=1)


class Proventos(models.Model):
    opcoes_tipos_provento = (('P', 'PROVENTO'), ('D', 'DESCONTO'), ('R', 'RESSARCIMENTO'))
    tipo = models.CharField("Tipo do Provento:", max_length=1, null=False, default='C', choices=opcoes_tipos_provento, error_messages=MENSAGENS_ERROS)
    nome = models.CharField("Nome:", max_length=100, null=False, error_messages=MENSAGENS_ERROS)
    descricao = models.CharField("Descrição:", max_length=500, null=True,blank=True, error_messages=MENSAGENS_ERROS)
    valor = models.DecimalField("Valor:", max_digits=7, decimal_places=2, null=True, blank=False)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    cadastrado_por = models.ForeignKey(entidade, related_name='provento_cadastrado_por',  default=1)
    ultima_alteracao = models.DateTimeField(null=True, auto_now=True)
    alterado_por = models.ForeignKey(entidade, related_name='provento_alterado_por', default=1)
    ativo = models.BooleanField(default=True)